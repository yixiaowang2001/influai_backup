#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LVN评论生成测试工具

实现多层级评论生成功能，包括：
1. 广度生成：基于上一层级的评论生成多条同级子评论（不同态度的）
2. 深度生成：基于评论链生成更深层级的评论
3. 筛选重要评论：从同层级评论中筛选出重要评论

作者：InfluAI开发团队
创建时间：2025-01-27
"""

import sys
import os
import json
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

# 设置数据库环境变量
os.environ["DB_TYPE"] = "mysql"
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_PORT"] = "3306"
os.environ["MYSQL_USER"] = "root"
os.environ["MYSQL_PASSWORD"] = "influai"
os.environ["MYSQL_DATABASE"] = "influai"
os.environ["MYSQL_CHARSET"] = "utf8mb4"

from backend.models import Attitude
from backend.database import crud, models
from backend.ai_module.llm import chat
from backend.ai_module.llm_utils import parse_json_response
from backend.utils import get_logger

logger = get_logger(__name__)

# 全局用户管理器（模拟main.py中的user_manager）
class GlobalUserManager:
    def __init__(self):
        self.current_human_user = None
    
    def set_current_user(self, human_user):
        """设置当前用户（会覆盖之前的用户）"""
        self.current_human_user = human_user
        logger.info(f"设置当前用户: {human_user.username} (ID: {human_user.user_id})")
    
    def get_current_user(self):
        """获取当前用户"""
        return self.current_human_user

# 全局用户管理器实例
user_manager = GlobalUserManager()


def ensure_current_user_set():
    """
    确保当前用户已设置，如果没有则设置默认用户
    
    Returns:
        bool: 是否成功设置或已存在当前用户
    """
    # 如果已经有当前用户，直接返回
    if user_manager.get_current_user():
        return True
    
    # 如果没有当前用户，设置默认用户
    try:
        from backend.database.database import get_db
        db = next(get_db())
        
        # 尝试获取用户ID为1的用户
        human_user = crud.get_human_user_by_id(db, 1)
        if not human_user:
            logger.error("未找到默认用户ID: 1")
            return False
        
        user_manager.set_current_user(human_user)
        logger.info(f"自动设置当前用户: {human_user.username} (ID: {human_user.user_id})")
        return True
        
    except Exception as e:
        logger.error(f"设置当前用户失败: {e}")
        return False


def get_breadth_generation_prompt(
    persona: str,
    post_content: str,
    parent_comment_content: str,
    parent_comment_attitude: str,
    is_human_user: bool,
    grandparent_comment_content: Optional[str] = None
) -> Tuple[str, str]:
    """
    生成广度生成LVN评论的prompt
    
    Args:
        persona: 人设描述
        post_content: 帖子内容
        parent_comment_content: 上级评论内容
        parent_comment_attitude: 上级评论态度
        is_human_user: 上级评论是否是人类用户
        grandparent_comment_content: 上级评论的上级评论内容（如果有）
        
    Returns:
        Tuple[str, str]: (system_prompt, user_prompt)
    """
    
    # 根据父评论态度确定生成策略
    attitude_strategy = get_attitude_generation_strategy(parent_comment_attitude)
    
    # 构建上下文信息
    context_info = f"""
帖子内容：{post_content}

上级评论内容：{parent_comment_content}
上级评论态度：{parent_comment_attitude}
上级评论类型：{'人类用户' if is_human_user else 'AI用户'}
"""
    
    if grandparent_comment_content:
        context_info += f"上级评论的上级评论：{grandparent_comment_content}\n"
    
    system_prompt = f"""你是一个专业的社交媒体评论生成助手。你的任务是模拟其他AI用户对上级评论的看法，生成多条不同态度的子评论。

人设信息：{persona}

生成要求：
1. 模拟其他AI用户对上级评论的反应，不是发帖者的视角
2. 根据上级评论的态度，主要生成方向一致和完全相反的评论
3. 生成策略：{attitude_strategy}
4. 评论内容要自然、真实，符合社交媒体用户的表达习惯
5. 每条评论都要有明确的态度倾向
6. 生成数量要合理，确保有衰减效果

态度类型说明：
- 极差态度：强烈反对、批评、讽刺
- 不友善态度：质疑、怀疑、轻微批评
- 中立态度：客观分析、中性观点
- 友善态度：支持、赞同、正面回应
- 极好态度：热情支持、赞美、强烈赞同
- 狂热态度：极度兴奋、崇拜、过度赞美

请按照上述策略生成不同态度的评论。"""

    user_prompt = f"""请基于以下信息生成多条不同态度的子评论：

{context_info}

请按照生成策略生成符合人设的、针对上级评论的不同态度回复。

返回格式为JSON：
{{
    "comments": [
        {{
            "attitude": "态度类型",
            "content": "评论内容"
        }}
    ]
}}"""

    return system_prompt, user_prompt


def get_attitude_generation_strategy(parent_attitude: str) -> str:
    """
    根据父评论态度确定生成策略
    
    Args:
        parent_attitude: 父评论态度
        
    Returns:
        str: 生成策略描述
    """
    # 态度映射
    attitude_map = {
        "极差": "BAD",
        "不友善": "NEUTRAL_NEGATIVE", 
        "中立": "NEUTRAL",
        "友善": "NEUTRAL_POSITIVE",
        "极好": "GOOD",
        "狂热": "PERFECT"
    }
    
    # 根据父评论态度确定主要生成的态度
    if parent_attitude in ["狂热", "极好", "友善"]:
        # 正面态度，主要生成方向一致和完全相反的
        return "主要生成狂热、极好、友善（方向一致）和极差、不友善（完全相反）的评论，少量中立评论"
    elif parent_attitude in ["极差", "不友善"]:
        # 负面态度，主要生成方向一致和完全相反的
        return "主要生成极差、不友善（方向一致）和狂热、极好、友善（完全相反）的评论，少量中立评论"
    else:
        # 中立态度，生成各种态度的评论
        return "生成各种态度的评论，包括极差、不友善、中立、友善、极好、狂热"


def breadth_generate_lvn_comments(
    post_id: int,
    parent_comment_id: int,
    retry: int = 5
) -> Dict[str, List[str]]:
    """
    广度生成：基于上一层级的评论生成多条同级子评论（不同态度的）
    
    Args:
        post_id: 帖子ID（获取帖子内容）
        parent_comment_id: 上级评论ID（获取评论态度、评论内容、上级评论是否是人类用户、上级评论的上级评论）
        retry: 重试次数（默认=5）
        
    Returns:
        Dict[str, List[str]]: 按态度分类的评论字典，如{"极差": [], "狂热": []}
    """
    try:
        # 确保当前用户已设置
        if not ensure_current_user_set():
            logger.error("无法设置当前用户")
            return {}
        
        # 获取当前用户和模板
        current_user = user_manager.get_current_user()
        from backend.database.database import get_db
        db = next(get_db())
        
        template = crud.get_user_template_by_id(db, current_user.user_template_id)
        if not template:
            logger.error(f"未找到用户模板ID: {current_user.user_template_id}")
            return {}
        
        persona = template.persona
        
        # 获取帖子内容
        post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
        if not post:
            logger.error(f"未找到帖子ID: {post_id}")
            return {}
        
        post_content = post.post_content
        
        # 获取上级评论信息
        parent_comment = db.query(models.Comment).filter(models.Comment.comment_id == parent_comment_id).first()
        if not parent_comment:
            logger.error(f"未找到上级评论ID: {parent_comment_id}")
            return {}
        
        parent_comment_content = parent_comment.comment_content
        is_human_user = parent_comment.sender_type == "human_user"
        
        # 获取上级评论的态度
        parent_comment_attitude = "未知"
        if not is_human_user:
            # 如果是AI用户，从AI用户信息中获取态度
            ai_user = crud.get_ai_user(db, parent_comment.sender_id)
            if ai_user:
                # 根据attitude_value确定态度类型
                attitude_value = ai_user.attitude_value
                if attitude_value <= -0.8:
                    parent_comment_attitude = "极差"
                elif attitude_value <= -0.4:
                    parent_comment_attitude = "不友善"
                elif attitude_value <= 0.4:
                    parent_comment_attitude = "中立"
                elif attitude_value <= 0.8:
                    parent_comment_attitude = "友善"
                else:
                    parent_comment_attitude = "极好"
        else:
            parent_comment_attitude = "人类用户评论"
        
        # 获取上级评论的上级评论（如果有）
        grandparent_comment_content = None
        if parent_comment.master_comment_id:
            grandparent_comment = db.query(models.Comment).filter(
                models.Comment.comment_id == parent_comment.master_comment_id
            ).first()
            if grandparent_comment:
                grandparent_comment_content = grandparent_comment.comment_content
        
        # 生成prompt
        system_prompt, user_prompt = get_breadth_generation_prompt(
            persona=persona,
            post_content=post_content,
            parent_comment_content=parent_comment_content,
            parent_comment_attitude=parent_comment_attitude,
            is_human_user=is_human_user,
            grandparent_comment_content=grandparent_comment_content
        )
        
        # 调用大模型生成评论
        logger.info(f"开始广度生成LVN评论，上级评论ID: {parent_comment_id}")
        
        for i in range(retry):
            response = chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config_type="comment"
            )
            
            if not response:
                logger.warning(f"收到空的广度生成响应，第{i + 1}次尝试")
                continue
                
            json_response = parse_json_response(response, {})
            if json_response and "comments" in json_response:
                comments = json_response["comments"]
                if comments:
                    # 按态度分类评论
                    result = organize_comments_by_attitude(comments)
                    logger.info(f"成功生成{len(comments)}条广度LVN评论")
                    return result
                    
            logger.warning(f"广度生成LVN评论失败，第{i + 1}次重试")
        
        logger.warning(f"广度生成LVN评论失败，未找到有效评论")
        return {}
        
    except Exception as e:
        logger.error(f"广度生成LVN评论异常: {e}")
        return {}


def organize_comments_by_attitude(comments: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """
    将评论按态度分类
    
    Args:
        comments: 评论列表，每个评论包含attitude和content字段
        
    Returns:
        Dict[str, List[str]]: 按态度分类的评论字典
    """
    # 初始化所有态度的空列表
    result = {
        "极差": [],
        "不友善": [],
        "中立": [],
        "友善": [],
        "极好": [],
        "狂热": []
    }
    
    # 态度映射（处理可能的变体）
    attitude_mapping = {
        "极差态度": "极差",
        "不友善态度": "不友善", 
        "中立态度": "中立",
        "友善态度": "友善",
        "极好态度": "极好",
        "狂热态度": "狂热",
        "极差": "极差",
        "不友善": "不友善",
        "中立": "中立", 
        "友善": "友善",
        "极好": "极好",
        "狂热": "狂热"
    }
    
    for comment in comments:
        attitude = comment.get("attitude", "").strip()
        content = comment.get("content", "").strip()
        
        if not content:
            continue
            
        # 映射态度到标准格式
        mapped_attitude = attitude_mapping.get(attitude, "中立")
        result[mapped_attitude].append(content)
    
    return result


def test_breadth_generation():
    """测试广度生成功能"""
    print("=" * 80)
    print("测试广度生成LVN评论功能")
    print("=" * 80)
    
    # 测试参数
    post_id = 1
    parent_comment_id = 1
    retry = 3
    
    print(f"测试参数：")
    print(f"  帖子ID：{post_id}")
    print(f"  上级评论ID：{parent_comment_id}")
    print(f"  重试次数：{retry}")
    print()
    
    # 执行广度生成
    comments_by_attitude = breadth_generate_lvn_comments(
        post_id=post_id,
        parent_comment_id=parent_comment_id,
        retry=retry
    )
    
    if comments_by_attitude:
        total_comments = sum(len(comments) for comments in comments_by_attitude.values())
        print(f"成功生成{total_comments}条广度LVN评论：")
        print("-" * 60)
        
        for attitude, comments in comments_by_attitude.items():
            if comments:
                print(f"{attitude}态度 ({len(comments)}条)：")
                for i, comment in enumerate(comments, 1):
                    print(f"  {i}. {comment}")
                print()
    else:
        print("广度生成失败，未生成任何评论")
    
    print("=" * 80)


def test_current_user_info():
    """测试当前用户信息获取"""
    print("=" * 80)
    print("测试当前用户信息获取")
    print("=" * 80)
    
    # 确保当前用户已设置
    if not ensure_current_user_set():
        print("设置当前用户失败")
        return
    
    # 获取当前用户信息
    current_user = user_manager.get_current_user()
    if current_user:
        print(f"当前用户信息：")
        print(f"  用户ID：{current_user.user_id}")
        print(f"  用户名：{current_user.username}")
        print(f"  用户模板ID：{current_user.user_template_id}")
        print(f"  粉丝数：{current_user.follower_count}")
        print(f"  创建时间：{current_user.created_at}")
        
        # 获取用户模板信息
        try:
            from backend.database.database import get_db
            db = next(get_db())
            template = crud.get_user_template_by_id(db, current_user.user_template_id)
            if template:
                print(f"  人设模板：{template.template_name}")
                print(f"  人设描述：{template.persona[:100]}...")
            else:
                print("  人设模板：未找到")
        except Exception as e:
            print(f"  获取模板信息失败：{e}")
    else:
        print("未设置当前用户")
    
    print("=" * 80)


def test_prompt_generation():
    """测试prompt生成功能"""
    print("=" * 80)
    print("测试prompt生成功能")
    print("=" * 80)
    
    # 确保当前用户已设置
    if not ensure_current_user_set():
        print("设置当前用户失败，无法继续测试")
        return
    
    # 获取当前用户的人设
    current_user = user_manager.get_current_user()
    try:
        from backend.database.database import get_db
        db = next(get_db())
        template = crud.get_user_template_by_id(db, current_user.user_template_id)
        if not template:
            print("未找到用户模板")
            return
        persona = template.persona
    except Exception as e:
        print(f"获取用户模板失败：{e}")
        return
    
    # 测试参数
    post_content = "开篇先聊粉底液！对比YSL、Armani和DW：YSL轻薄适合干皮，Armani遮瑕强更控油，DW持妆最稳但妆效厚重。你们最常用哪一款？"
    parent_comment_content = ("哇咧，追更博主的测评简直是我每天的任务，这篇文章真的让我的心又开始种草跳动！YSL和Armani"
                              "完全是两种风格好吗，看着它们脑海里瞬间浮现自己初学化妆的样子……真的太感慨了！！必须再次表白博主爱死你啦！")
    parent_comment_attitude = "狂热"
    is_human_user = False
    grandparent_comment_content = None
    
    print(f"测试参数：")
    print(f"  人设：{persona[:100]}...")
    print(f"  帖子内容：{post_content}")
    print(f"  上级评论内容：{parent_comment_content}")
    print(f"  上级评论态度：{parent_comment_attitude}")
    print(f"  是否人类用户：{is_human_user}")
    print(f"  上级评论的上级评论：{grandparent_comment_content}")
    print()
    
    # 生成prompt
    system_prompt, user_prompt = get_breadth_generation_prompt(
        persona=persona,
        post_content=post_content,
        parent_comment_content=parent_comment_content,
        parent_comment_attitude=parent_comment_attitude,
        is_human_user=is_human_user,
        grandparent_comment_content=grandparent_comment_content
    )
    
    print("生成的System Prompt：")
    print("-" * 60)
    print(system_prompt)
    print()
    
    print("生成的User Prompt：")
    print("-" * 60)
    print(user_prompt)
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    print("LVN评论生成测试工具")
    print("=" * 80)
    
    try:
        # 测试当前用户信息获取
        test_current_user_info()
        
        # 测试prompt生成
        test_prompt_generation()
        
        # 测试广度生成
        test_breadth_generation()
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

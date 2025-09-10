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
from typing import List, Dict, Optional, Tuple

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

# 设置数据库环境变量
os.environ.update({
    "DB_TYPE": "mysql",
    "MYSQL_HOST": "localhost",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "root",
    "MYSQL_PASSWORD": "influai",
    "MYSQL_DATABASE": "influai",
    "MYSQL_CHARSET": "utf8mb4"
})

from backend.models import Attitude
from backend.database import crud, models
from backend.ai_module.llm import chat
from backend.ai_module.llm_utils import parse_json_response
from backend.utils import get_logger

logger = get_logger(__name__)

# 全局用户管理器
class GlobalUserManager:
    def __init__(self):
        self.current_human_user = None
    
    def set_current_user(self, human_user):
        """设置当前用户"""
        self.current_human_user = human_user
        logger.info(f"设置当前用户: {human_user.username} (ID: {human_user.user_id})")
    
    def get_current_user(self):
        """获取当前用户"""
        return self.current_human_user

user_manager = GlobalUserManager()

# 态度映射常量
ATTITUDE_MAPPING = {
    "极差态度": "极差", "不友善态度": "不友善", "友善态度": "友善",
    "极好态度": "极好", "狂热态度": "狂热",
    "极差": "极差", "不友善": "不友善", "友善": "友善",
    "极好": "极好", "狂热": "狂热"
}

ATTITUDE_TYPES = ["极差", "不友善", "友善", "极好", "狂热"]


def ensure_current_user_set():
    """确保当前用户已设置，如果没有则设置默认用户"""
    if user_manager.get_current_user():
        return True
    
    try:
        from backend.database.database import get_db
        db = next(get_db())
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


def get_attitude_generation_strategy(parent_attitude: str) -> str:
    """根据父评论态度确定生成策略"""
    if parent_attitude in ["狂热", "极好", "友善"]:
        return "主要生成狂热、极好、友善（方向一致）和极差、不友善（完全相反）的评论"
    elif parent_attitude in ["极差", "不友善"]:
        return "主要生成极差、不友善（方向一致）和狂热、极好、友善（完全相反）的评论"
    else:
        return "生成各种态度的评论，包括极差、不友善、友善、极好、狂热"


def get_breadth_generation_prompt(
    persona: str,
    post_content: str,
    parent_comment_content: str,
    parent_comment_attitude: str,
    is_human_user: bool,
    comment_count: int,
    grandparent_comment_content: Optional[str] = None
) -> Tuple[str, str]:
    """生成广度生成LVN评论的prompt"""
    attitude_strategy = get_attitude_generation_strategy(parent_comment_attitude)
    
    context_info = f"""帖子内容：{post_content}

上级评论内容：{parent_comment_content}
上级评论态度：{parent_comment_attitude}
上级评论类型：{'人类用户' if is_human_user else 'AI用户'}

帖子评论数：{comment_count}条"""
    
    if grandparent_comment_content:
        context_info += f"\n上级评论的上级评论：{grandparent_comment_content}"
    
    system_prompt = f"""你是一个专业的社交媒体评论生成助手。你的任务是模拟其他AI用户对发帖博主的看法，生成多条不同态度的子评论。

人设信息：{persona}

生成要求：
1. 模拟其他AI用户对发帖博主的反应，不是发帖者的视角
2. 根据上级评论的态度，主要生成方向一致和完全相反的评论
3. 生成策略：{attitude_strategy}
4. 评论内容要自然、真实，符合社交媒体用户的表达习惯
5. 每条评论都要有明确的态度倾向，双方攻击性要强一些
6. 根据帖子的评论数（{comment_count}条）自己决定生成总数和态度分布，不要数量均匀生成
7. 生成总数可以取决于帖子的评论数，分布要符合社交媒体的真实情况
8. 不要生成中立评论，只生成有明确立场和攻击性的评论

态度类型说明（都是对发帖博主的态度）：
- 极差态度：对博主强烈反对、批评、讽刺、攻击性很强（会间接攻击支持博主的父评论）
- 不友善态度：对博主质疑、怀疑、轻微批评、有一定攻击性
- 友善态度：对博主支持、赞同、正面回应，但要有一定攻击性
- 极好态度：对博主热情支持、赞美、强烈赞同，攻击性较强
- 狂热态度：对博主极度兴奋、崇拜、过度赞美，攻击性很强

请根据帖子评论数和父评论态度，自己决定生成总数和各态度的分布，确保双方都有较强的攻击性，不要生成中立评论。"""

    user_prompt = f"""请基于以下信息生成多条不同态度的子评论：

{context_info}

请按照生成策略生成符合人设的、针对发帖博主的不同态度回复。

重要提醒：
- 所有态度都是对发帖博主的，不是对上级评论的
- 极差态度：对博主有极差态度，会攻击博主，间接也会攻击支持博主的上级评论
- 不友善态度：对博主不友善，质疑博主
- 友善态度：对博主友善，支持上级评论
- 极好态度：对博主极好，支持上级评论  
- 狂热态度：对博主狂热，支持上级评论
- 回复可以围绕上级评论提到的产品（如YSL、Armani）来展开对博主的评价
- 确保回复内容与上级评论内容高度相关

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


def get_parent_comment_attitude(parent_comment, db):
    """获取上级评论的态度"""
    if parent_comment.sender_type == "human_user":
        return "人类用户评论"
    
    ai_user = crud.get_ai_user(db, parent_comment.sender_id)
    if not ai_user:
        return "未知"
    
    attitude_value = ai_user.attitude_value
    if attitude_value <= -0.8:
        return "极差"
    elif attitude_value <= -0.4:
        return "不友善"
    elif attitude_value <= 0.4:
        return "中立"
    elif attitude_value <= 0.8:
        return "友善"
    else:
        return "极好"


def breadth_generate_lvn_comments(
    post_id: int,
    parent_comment_id: int,
    comment_count: int = 87,
    retry: int = 5
) -> Dict[str, List[str]]:
    """广度生成：基于上一层级的评论生成多条同级子评论（不同态度的）"""
    try:
        if not ensure_current_user_set():
            logger.error("无法设置当前用户")
            return {}
        
        # 获取数据库连接和用户信息
        current_user = user_manager.get_current_user()
        from backend.database.database import get_db
        db = next(get_db())
        
        template = crud.get_user_template_by_id(db, current_user.user_template_id)
        if not template:
            logger.error(f"未找到用户模板ID: {current_user.user_template_id}")
            return {}
        
        # 获取帖子内容
        post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
        if not post:
            logger.error(f"未找到帖子ID: {post_id}")
            return {}
        
        # 获取上级评论信息
        parent_comment = db.query(models.Comment).filter(models.Comment.comment_id == parent_comment_id).first()
        if not parent_comment:
            logger.error(f"未找到上级评论ID: {parent_comment_id}")
            return {}
        
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
            persona=template.persona,
            post_content=post.post_content,
            parent_comment_content=parent_comment.comment_content,
            parent_comment_attitude=get_parent_comment_attitude(parent_comment, db),
            is_human_user=parent_comment.sender_type == "human_user",
            comment_count=comment_count,
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
                    result = organize_comments_by_attitude(comments)
                    logger.info(f"成功生成{len(comments)}条广度LVN评论")
                    print_comments_json(result)
                    return result
                    
            logger.warning(f"广度生成LVN评论失败，第{i + 1}次重试")
        
        logger.warning(f"广度生成LVN评论失败，未找到有效评论")
        return {}
        
    except Exception as e:
        logger.error(f"广度生成LVN评论异常: {e}")
        return {}


def organize_comments_by_attitude(comments: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """将评论按态度分类"""
    result = {attitude: [] for attitude in ATTITUDE_TYPES}
    
    for comment in comments:
        attitude = comment.get("attitude", "").strip()
        content = comment.get("content", "").strip()
        
        if not content:
            continue
            
        mapped_attitude = ATTITUDE_MAPPING.get(attitude)
        if mapped_attitude:
            result[mapped_attitude].append(content)
    
    return result


def print_comments_json(comments_by_attitude: Dict[str, List[str]]) -> None:
    """打印评论JSON格式"""
    # 过滤掉空的列表
    filtered_result = {attitude: comments for attitude, comments in comments_by_attitude.items() if comments}
    
    print("生成的评论JSON格式：")
    print("=" * 80)
    print(json.dumps(filtered_result, ensure_ascii=False, indent=2))
    print("=" * 80)
    
    # 打印统计信息
    total_comments = sum(len(comments) for comments in comments_by_attitude.values())
    print(f"总生成评论数：{total_comments}")
    for attitude, comments in comments_by_attitude.items():
        if comments:
            print(f"{attitude}态度：{len(comments)}条")
    print("=" * 80)


def test_current_user_info():
    """测试当前用户信息获取"""
    print("=" * 80)
    print("测试当前用户信息获取")
    print("=" * 80)
    
    if not ensure_current_user_set():
        print("设置当前用户失败")
        return
    
    current_user = user_manager.get_current_user()
    if current_user:
        print(f"当前用户信息：")
        print(f"  用户ID：{current_user.user_id}")
        print(f"  用户名：{current_user.username}")
        print(f"  用户模板ID：{current_user.user_template_id}")
        print(f"  粉丝数：{current_user.follower_count}")
        print(f"  创建时间：{current_user.created_at}")
        
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
    test_params = {
        "post_content": "开篇先聊粉底液！对比YSL、Armani和DW：YSL轻薄适合干皮，Armani遮瑕强更控油，DW持妆最稳但妆效厚重。你们最常用哪一款？",
        "parent_comment_content": "哇咧，追更博主的测评简直是我每天的任务，这篇文章真的让我的心又开始种草跳动！YSL和Armani完全是两种风格好吗，看着它们脑海里瞬间浮现自己初学化妆的样子……真的太感慨了！！必须再次表白博主爱死你啦！",
        "parent_comment_attitude": "狂热",
        "is_human_user": False,
        "comment_count": 87,
        "grandparent_comment_content": None
    }
    
    print(f"测试参数：")
    print(f"  人设：{persona[:100]}...")
    for key, value in test_params.items():
        print(f"  {key}：{value}")
    print()
    
    # 生成prompt
    system_prompt, user_prompt = get_breadth_generation_prompt(
        persona=persona,
        **test_params
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


def test_breadth_generation():
    """测试广度生成功能"""
    print("=" * 80)
    print("测试广度生成LVN评论功能")
    print("=" * 80)
    
    # 测试参数
    test_params = {
        "post_id": 1,
        "parent_comment_id": 1,
        "comment_count": 87,
        "retry": 3
    }
    
    print(f"测试参数：")
    for key, value in test_params.items():
        print(f"  {key}：{value}")
    print()
    
    # 执行广度生成
    comments_by_attitude = breadth_generate_lvn_comments(**test_params)
    
    if comments_by_attitude:
        total_comments = sum(len(comments) for comments in comments_by_attitude.values())
        print(f"成功生成{total_comments}条广度LVN评论")
    else:
        print("广度生成失败，未生成任何评论")
    
    print("=" * 80)


if __name__ == "__main__":
    print("LVN评论生成测试工具")
    print("=" * 80)
    
    try:
        test_current_user_info()
        test_prompt_generation()
        test_breadth_generation()
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
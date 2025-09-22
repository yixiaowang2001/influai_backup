#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LVN深度评论生成测试工具

实现深度评论生成功能，包括：
1. 双人来回对话：两个用户来回吵架，深度较深，每层衍生对话通常不会很多
2. 多人参与对话：不同用户在进行回复，深度较浅，每层衍生对话会略多

作者：InfluAI开发团队
创建时间：2025-01-27
"""

import json
import os
import sys
from typing import List, Dict, Tuple

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

from backend.database import crud
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




def get_depth_generation_prompt(
    persona: str,
    post_content: str,
    parent_comment_content: str,
    parent_comment_attitude: str,
    is_human_user: bool,
    conversation_type: str,  # "双人来回对话" 或 "多人参与对话"
    retry: int = 5
) -> Tuple[str, str]:
    """生成深度生成LVN评论的prompt"""
    
    context_info = f"""帖子内容：{post_content}

上级评论内容：{parent_comment_content}
上级评论态度：{parent_comment_attitude}
上级评论类型：{'人类用户' if is_human_user else 'AI用户'}

对话类型：{conversation_type}"""
    
    if conversation_type == "双人来回对话":
        depth_desc = "深度较深，通常有3-7轮对话，每层衍生对话通常不会很多（1-3条）"
        user_strategy = "核心对话围绕用户A和用户B两个用户展开，可能会有其他用户进行附和"
        attack_desc = "双方攻击性要强，形成激烈的争论"
    else:  # 多人参与对话
        depth_desc = "深度较浅，通常有2-4轮对话，每层衍生对话会略多（5-8条）"
        user_strategy = "多个用户（用户A、用户B、用户C等）"
        attack_desc = "各方态度多样，攻击性相对较强"
    
    system_prompt = f"""你是一个专业的社交媒体深度对话生成助手。你的任务是模拟AI用户之间的深度对话，生成评论链。

人设信息：{persona}

生成要求：
1. 模拟{user_strategy}之间的对话，围绕上级评论展开讨论
2. 对话特点：
   - {depth_desc}，但每层可能有多条评论
   - {attack_desc}
   - 对话要有逻辑递进，不能简单重复
3. 对话内容要自然、真实，符合社交媒体用户的表达习惯
4. 每条评论都要有明确的态度倾向
5. 对话要围绕上级评论提到的内容展开，不能偏离主题
6. 确保对话有深度，每轮都要有新的观点或反驳

对话生成策略：
- 支持方：对博主持{parent_comment_attitude}态度，支持上级评论
- 质疑方：对博主持相反态度，质疑上级评论
- 对话本身要接近网络用语
- 每轮对话都要有新的论据或反驳点
- 对话要有层次感，从表面争论深入到本质分歧
- 每层可以有多条评论，不限制每层只有一条评论

请生成符合人设的、有深度的对话评论链。"""

    user_prompt = f"""请基于以下信息生成深度评论链：

{context_info}

请按照对话特点生成符合人设的、有深度的评论对话。

重要提醒：
- 生成深度对话，各方要有不同的观点和角度
- 对话要有深度，每轮都要有新的观点或反驳
- 围绕上级评论提到的内容来展开讨论
- 确保对话内容与上级评论内容高度相关
- 对话要有逻辑递进，不能简单重复

返回格式为JSON：
{{
    "评论链": [
        {{
            "层级": 1,
            "评论": [
                {{
                    "用户A": "评论内容1",
                    "态度": "极好"
                }},
                {{
                    "用户B": "评论内容2", 
                    "态度": "极差"
                }}
            ]
        }},
        {{
            "层级": 2,
            "评论": [
                {{
                    "用户A": "评论内容3",
                    "态度": "狂热"
                }},
                {{
                    "用户B": "评论内容4",
                    "态度": "不友善"
                }},
                {{
                    "用户C": "评论内容5",
                    "态度": "友善"
                }}
            ]
        }},
        {{
            "层级": 3,
            "评论": [
                {{
                    "用户A": "评论内容6",
                    "态度": "极好"
                }},
                {{
                    "用户B": "评论内容7",
                    "态度": "极差"
                }}
            ]
        }}
    ]
}}"""

    return system_prompt, user_prompt


def depth_generate_lvn_comments(
    post_content: str,
    parent_comment_content: str,
    parent_comment_attitude: str = "狂热",
    is_human_user: bool = False,
    conversation_type: str = "双人来回对话",  # "双人来回对话" 或 "多人参与对话"
    retry: int = 5
) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """深度生成：基于上一层级的评论生成子评论对话（不同级）"""
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
        
        # 生成prompt
        system_prompt, user_prompt = get_depth_generation_prompt(
            persona=template.persona,
            post_content=post_content,
            parent_comment_content=parent_comment_content,
            parent_comment_attitude=parent_comment_attitude,
            is_human_user=is_human_user,
            conversation_type=conversation_type,
            retry=retry
        )
        
        # 调用大模型生成评论
        logger.info(f"开始深度生成LVN评论，对话类型: {conversation_type}")
        
        for i in range(retry):
            response = chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config_type="comment"
            )
            
            if not response:
                logger.warning(f"收到空的深度生成响应，第{i + 1}次尝试")
                continue
                
            json_response = parse_json_response(response, {})
            if json_response and "评论链" in json_response:
                result = json_response["评论链"]
                if result and isinstance(result, list) and len(result) > 0:
                    total_comments = sum(len(level.get("评论", [])) for level in result)
                    logger.info(f"成功生成{len(result)}个层级，共{total_comments}条深度LVN评论")
                    print_comments_json({"评论链": result})
                    return {"评论链": result}
                    
            logger.warning(f"深度生成LVN评论失败，第{i + 1}次重试")
        
        logger.warning(f"深度生成LVN评论失败，未找到有效评论")
        return {}
        
    except Exception as e:
        logger.error(f"深度生成LVN评论异常: {e}")
        return {}


def print_comments_json(comments_result: Dict[str, List[Dict[str, any]]]) -> None:
    """打印评论JSON格式"""
    print("生成的深度评论JSON格式：")
    print("=" * 80)
    print(json.dumps(comments_result, ensure_ascii=False, indent=2))
    print("=" * 80)
    
    # 打印统计信息
    for key, levels in comments_result.items():
        if key == "评论链" and isinstance(levels, list):
            total_comments = 0
            attitude_count = {}
            
            print(f"评论链统计：")
            for i, level in enumerate(levels, 1):
                if isinstance(level, dict) and "评论" in level:
                    level_comments = level["评论"]
                    level_count = len(level_comments)
                    total_comments += level_count
                    print(f"  层级{i}：{level_count}条评论")
                    
                    # 统计各态度的评论数量
                    for comment in level_comments:
                        if isinstance(comment, dict) and "态度" in comment:
                            attitude = comment["态度"]
                            attitude_count[attitude] = attitude_count.get(attitude, 0) + 1
            
            print(f"总评论数：{total_comments}条")
            
            if attitude_count:
                print("态度分布：")
                for attitude, count in attitude_count.items():
                    print(f"  {attitude}：{count}条")
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
    print("测试深度生成prompt生成功能")
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
        "post_content": "煞笔公司……不想干了，压力太大了。累死累活还不如一个臭写代码的",
        "parent_comment_content": "哇咧，追更博主的测评简直是我每天的任务，这篇文章真的让我的心又开始种草跳动！YSL和Armani完全是两种风格好吗，看着它们脑海里瞬间浮现自己初学化妆的样子……真的太感慨了！！必须再次表白博主爱死你啦！",
        "parent_comment_attitude": "狂热",
        "is_human_user": False,
        "conversation_type": "双人来回对话",
        "retry": 5
    }
    
    print(f"测试参数：")
    print(f"  人设：{persona[:100]}...")
    for key, value in test_params.items():
        print(f"  {key}：{value}")
    print()
    
    # 生成prompt
    system_prompt, user_prompt = get_depth_generation_prompt(
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


def test_depth_generation_dual():
    """测试双人来回对话深度生成功能"""
    print("=" * 80)
    print("测试双人来回对话深度生成LVN评论功能")
    print("=" * 80)
    
    # 测试参数
    test_params = {
        "post_content": "开篇先聊粉底液！对比YSL、Armani和DW：YSL轻薄适合干皮，Armani遮瑕强更控油，DW持妆最稳但妆效厚重。你们最常用哪一款？",
        "parent_comment_content": "哇咧，追更博主的测评简直是我每天的任务，这篇文章真的让我的心又开始种草跳动！YSL和Armani完全是两种风格好吗，看着它们脑海里瞬间浮现自己初学化妆的样子……真的太感慨了！！必须再次表白博主爱死你啦！",
        "parent_comment_attitude": "狂热",
        "is_human_user": False,
        "conversation_type": "双人来回对话",
        "retry": 3
    }
    
    print(f"测试参数：")
    for key, value in test_params.items():
        if key in ["post_content", "parent_comment_content"]:
            print(f"  {key}：{value[:50]}...")
        else:
            print(f"  {key}：{value}")
    print()
    
    # 执行深度生成
    comments_result = depth_generate_lvn_comments(**test_params)
    
    if comments_result:
        print("成功生成双人来回对话深度评论")
    else:
        print("双人来回对话深度生成失败，未生成任何评论")
    
    print("=" * 80)


def test_depth_generation_multi():
    """测试多人参与对话深度生成功能"""
    print("=" * 80)
    print("测试多人参与对话深度生成LVN评论功能")
    print("=" * 80)
    
    # 测试参数
    test_params = {
        "post_content": "开篇先聊粉底液！对比YSL、Armani和DW：YSL轻薄适合干皮，Armani遮瑕强更控油，DW持妆最稳但妆效厚重。你们最常用哪一款？",
        "parent_comment_content": "哇咧，追更博主的测评简直是我每天的任务，这篇文章真的让我的心又开始种草跳动！YSL和Armani完全是两种风格好吗，看着它们脑海里瞬间浮现自己初学化妆的样子……真的太感慨了！！必须再次表白博主爱死你啦！",
        "parent_comment_attitude": "狂热",
        "is_human_user": False,
        "conversation_type": "多人参与对话",
        "retry": 3
    }
    
    print(f"测试参数：")
    for key, value in test_params.items():
        if key in ["post_content", "parent_comment_content"]:
            print(f"  {key}：{value[:50]}...")
        else:
            print(f"  {key}：{value}")
    print()
    
    # 执行深度生成
    comments_result = depth_generate_lvn_comments(**test_params)
    
    if comments_result:
        print("成功生成多人参与对话深度评论")
    else:
        print("多人参与对话深度生成失败，未生成任何评论")
    
    print("=" * 80)


if __name__ == "__main__":
    print("LVN深度评论生成测试工具")
    print("=" * 80)
    
    try:
        test_current_user_info()
        test_prompt_generation()
        test_depth_generation_dual()
        test_depth_generation_multi()
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

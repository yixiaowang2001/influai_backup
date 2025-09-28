#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LVN评论生成测试工具 - 极简版

只保留核心参数获取功能，用于调试prompt

作者：InfluAI开发团队
创建时间：2025-01-27
"""

import sys
import os
from typing import Dict
from backend.models.attitude import Attitude

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

from backend.database import crud, models
from backend.ai_module.llm import chat
from backend.utils import get_logger

logger = get_logger(__name__)


# 全局用户管理器
class GlobalUserManager:
    def __init__(self):
        self.current_human_user = None

    def set_current_user(self, human_user):
        """设置当前用户"""
        self.current_human_user = human_user

    def get_current_user(self):
        """获取当前用户"""
        return self.current_human_user


user_manager = GlobalUserManager()


def ensure_current_user_set():
    """确保当前用户已设置，如果没有则设置默认用户"""
    if user_manager.get_current_user():
        return True

    try:
        from backend.database.database import get_db
        db = next(get_db())
        human_user = crud.get_human_user_by_id(db, 1)
        if not human_user:
            return False

        user_manager.set_current_user(human_user)
        return True
    except Exception as e:
        return False


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


def get_test_parameters(post_id: int, parent_comment_id: int, comment_count: int = 87) -> Dict:
    """获取测试所需的所有参数"""
    try:
        if not ensure_current_user_set():
            return {}

        # 获取数据库连接和用户信息
        current_user = user_manager.get_current_user()
        from backend.database.database import get_db
        db = next(get_db())

        template = crud.get_user_template_by_id(db, current_user.user_template_id)
        if not template:
            return {}

        # 获取帖子内容
        post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
        if not post:
            return {}

        # 获取上级评论信息
        parent_comment = db.query(models.Comment).filter(models.Comment.comment_id == parent_comment_id).first()
        if not parent_comment:
            return {}

        # 获取上级评论的上级评论（如果有）
        grandparent_comment_content = None
        if parent_comment.master_comment_id:
            grandparent_comment = db.query(models.Comment).filter(
                models.Comment.comment_id == parent_comment.master_comment_id
            ).first()
            if grandparent_comment:
                grandparent_comment_content = grandparent_comment.comment_content

        # 组装所有参数
        parameters = {
            "persona": template.persona,
            "post_content": post.post_content,
            "parent_comment_content": parent_comment.comment_content,
            "parent_comment_attitude": get_parent_comment_attitude(parent_comment, db),
            "is_human_user": parent_comment.sender_type == "human_user",
            "comment_count": comment_count,
            "grandparent_comment_content": grandparent_comment_content,
            "current_user": {
                "user_id": current_user.user_id,
                "username": current_user.username,
                "user_template_id": current_user.user_template_id,
                "follower_count": current_user.follower_count
            },
            "post": {
                "post_id": post.post_id,
                "post_content": post.post_content,
                "created_at": str(post.created_at)
            },
            "parent_comment": {
                "comment_id": parent_comment.comment_id,
                "comment_content": parent_comment.comment_content,
                "sender_type": parent_comment.sender_type,
                "sender_id": parent_comment.sender_id,
                "master_comment_id": parent_comment.master_comment_id
            }
        }

        return parameters

    except Exception as e:
        return {}


if __name__ == "__main__":
    # 获取参数
    parameters = get_test_parameters(post_id=1, parent_comment_id=1, comment_count=87)

    if not parameters:
        print("获取参数失败")
        exit(1)

    # 基本的prompt模板
    system_prompt = f"""你是一个专业的社交媒体评论生成助手。你的任务是模拟网友们对博主的帖子的一级评论的看法，针对该条一级评论，生成多条该一级评论的二级评论。

# 生成要求
1. 可参考的内容：博主人设，博主帖子内容，上级评论内容，上级评论态度，上级评论者（是否为博主）。
2. 生成多条长短不一，攻击性强，情绪明确强烈的子评论。
3. 评论内容要自然、真实，符合社交媒体用户的表达习惯。
4. 根据帖子的评论数（{parameters['comment_count']}条），自主决定生成总数。
5. 子评论长短不一，可以为短、一针见血、情绪强烈的（8字以内）；也可以为长但诉说、情绪强烈的（8字以上）。
6. 生成内容需要严格符合返回格式。

# 态度类型
{list(Attitude)}

# 返回格式
返回格式为JSON：
{{
    "comments": [
        {{
    "attitude": "态度类型",
            "content": "评论内容"
        }}
    ]
}}
"""

    user_prompt = f"""请基于以下信息生成多条子评论：
# 博主人设
{parameters['persona']}

# 博主帖子内容
{parameters['post_content']}

# 上级评论内容
{parameters['parent_comment_content']}

# 上级评论态度
{parameters['parent_comment_attitude']}

# 上级评论者
{'博主' if parameters['is_human_user'] else '网友'}

# 帖子评论数
{parameters['comment_count']}条
"""

    if parameters['grandparent_comment_content']:
        user_prompt += f"\n# 上级评论的上级评论\n\n{parameters['grandparent_comment_content']}"

    # 调用大模型生成评论
    print("开始调用大模型生成评论...")
    print("=" * 80)

    response = chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        config_type="comment"
    )

    print("大模型响应：")
    print("=" * 80)
    print(response)
    print("=" * 80)

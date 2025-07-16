from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class HumanUser:
    """人类用户数据模型"""
    user_id: int
    username: str
    avatar_path: str = ""
    persona: str = ""
    description: str = ""
    follower_count: int = 0
    history_posts: Optional[List] = None
    created_at: Optional[datetime] = None

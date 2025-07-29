from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class HumanUser:
    """人类用户数据模型"""
    user_id: int
    username: str
    user_template_id: int
    avatar_path: str = ""
    follower_count: int = 0
    created_at: Optional[datetime] = None

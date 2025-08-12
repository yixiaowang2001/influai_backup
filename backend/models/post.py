from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Post:
    """帖子数据模型"""
    post_content: str
    post_id: Optional[int] = None
    like_count: Optional[int] = None
    is_human_user_liked: Optional[int] = 0
    created_at: datetime = datetime.now()

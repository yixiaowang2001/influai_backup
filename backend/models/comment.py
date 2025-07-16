from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .enums import Attitude


@dataclass
class Comment:
    """评论数据模型"""
    comment_content: str
    comment_user_type: int
    comment_attitude: Attitude
    comment_level: int
    post_id: Optional[int] = None
    comment_likes: int = 0
    comment_id: Optional[str] = None
    comment_user_id: Optional[str] = None
    master_comment_id: Optional[str] = None
    created_at: datetime = datetime.now()
    send_at: Optional[datetime] = None

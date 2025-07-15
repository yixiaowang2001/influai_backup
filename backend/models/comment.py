from dataclasses import dataclass
from datetime import datetime

from .enums import Attitude


@dataclass
class Comment:
    comment_content: str
    comment_user_type: int
    comment_attitude: Attitude
    comment_level: int
    post_id: int = None
    comment_likes: int = 0
    comment_id: str = None
    comment_user_id: str = None
    master_comment_id: str = None
    created_at: datetime = datetime.now()
    send_at: datetime = None

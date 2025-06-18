from dataclasses import dataclass
from datetime import datetime

from .enums import Attitude


@dataclass
class Comment:
    comment_id: str
    comment_content: str
    comment_user_type: str
    comment_user_id: str
    comment_attitude: Attitude
    comment_level: int
    master_comment_id: str
    created_at: datetime

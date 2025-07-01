from dataclasses import dataclass
from datetime import datetime


@dataclass
class Post:
    post_content: str
    post_id: int = None
    like_count: int = None
    comments: list = None
    created_at: datetime = None
    edited_at: datetime = None

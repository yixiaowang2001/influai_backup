from dataclasses import dataclass
from datetime import datetime


@dataclass
class Post:
    post_id: int
    post_content: str
    repost_count: list  # 后续支持详细repost，替换成reposts
    like_count: int
    comments: list
    upvote_count: int
    created_at: datetime = None
    edited_at: datetime = None

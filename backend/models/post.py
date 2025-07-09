from dataclasses import dataclass
from datetime import datetime


@dataclass
class Post:
    post_content: str
    post_id: int = None
    like_count: int = None
    created_at: datetime = datetime.now()

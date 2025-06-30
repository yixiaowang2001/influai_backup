from dataclasses import dataclass
from datetime import datetime


@dataclass
class HumanUser:
    user_id: int
    username: str
    avatar_path: str = ""
    persona: str = ""
    description: str = ""
    follower_count: int = 0
    history_posts: list = None
    created_at: datetime = None

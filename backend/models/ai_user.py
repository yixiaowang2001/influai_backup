from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIUser:
    user_id: int
    username: str
    avatar_path: str = ""
    history_comments: list = None
    created_at: datetime = None
    attitude_value: float = 0.0

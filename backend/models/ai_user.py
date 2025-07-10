from dataclasses import dataclass
from datetime import datetime

from .enums import Attitude


@dataclass
class AIUser:
    username: str
    avatar_path: str = ""
    user_id: int = None
    history_comments: list = None
    created_at: datetime = None
    attitude_value: float = 0.0

    def __post_init__(self):
        self.attitude_type = Attitude.from_value(self.attitude_value)
        self.is_fan = True if self.attitude_value >= 0.5 else False

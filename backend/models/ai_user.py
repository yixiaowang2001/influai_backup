from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from .enums import Attitude


@dataclass
class AIUser:
    """AI用户数据模型"""
    username: str
    avatar_path: str = ""
    user_id: Optional[str] = None
    history_comments: Optional[List] = None
    created_at: Optional[datetime] = None
    attitude_value: float = 0.0

    def __post_init__(self):
        """初始化后处理"""
        self.attitude_type = Attitude.from_value(self.attitude_value)
        self.is_fan = True if self.attitude_value >= 0.5 else False

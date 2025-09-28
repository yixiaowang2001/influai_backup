"""
推送配置管理
简单的推送配置，支持评论和点赞两种类型
"""
from dataclasses import dataclass
from enum import Enum
from backend.configs.global_config import PUSH_CONFIG


class PushType(Enum):
    """推送类型枚举"""
    COMMENT = "comment"
    LIKE = "like"


@dataclass
class PushConfig:
    """推送配置"""
    push_type: PushType
    total_duration: int  # 总推送时间（秒）
    base_interval: float  # 基础间隔（秒）
    random_variance: float = 0.3  # 随机波动比例（默认30%）
    initial_delay: float = 0.5  # 初始延迟（秒）


class PushConfigManager:
    """推送配置管理器"""
    
    @classmethod
    def _get_config_from_global(cls, push_type: str) -> PushConfig:
        """从全局配置获取推送配置"""
        config_data = PUSH_CONFIG[push_type]
        return PushConfig(
            push_type=PushType(push_type),
            total_duration=config_data["total_duration"],
            base_interval=config_data["base_interval"],
            random_variance=config_data["random_variance"],
            initial_delay=config_data["initial_delay"]
        )
    
    # 默认配置（从全局配置读取）
    DEFAULT_COMMENT_CONFIG = None
    DEFAULT_LIKE_CONFIG = None
    
    @classmethod
    def _init_default_configs(cls):
        """初始化默认配置"""
        if cls.DEFAULT_COMMENT_CONFIG is None:
            cls.DEFAULT_COMMENT_CONFIG = cls._get_config_from_global("comment")
        if cls.DEFAULT_LIKE_CONFIG is None:
            cls.DEFAULT_LIKE_CONFIG = cls._get_config_from_global("like")
    
    @classmethod
    def get_default_comment_config(cls):
        """获取默认评论配置"""
        cls._init_default_configs()
        return cls.DEFAULT_COMMENT_CONFIG
    
    @classmethod
    def get_default_like_config(cls):
        """获取默认点赞配置"""
        cls._init_default_configs()
        return cls.DEFAULT_LIKE_CONFIG
    
    @classmethod
    def get_comment_config(cls, total_duration: int = 300, base_interval: float = 10.0) -> PushConfig:
        """获取评论推送配置"""
        return PushConfig(
            push_type=PushType.COMMENT,
            total_duration=total_duration,
            base_interval=base_interval,
            random_variance=0.3,
            initial_delay=1.0
        )
    
    @classmethod
    def get_like_config(cls, total_duration: int = 180, base_interval: float = 8.0) -> PushConfig:
        """获取点赞推送配置"""
        return PushConfig(
            push_type=PushType.LIKE,
            total_duration=total_duration,
            base_interval=base_interval,
            random_variance=0.3,
            initial_delay=0.5
        )

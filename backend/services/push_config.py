"""
推送配置管理
简单的推送配置，支持评论和点赞两种类型
"""
from dataclasses import dataclass
from enum import Enum


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
    
    # 默认配置
    DEFAULT_COMMENT_CONFIG = PushConfig(
        push_type=PushType.COMMENT,
        total_duration=300,  # 5分钟
        base_interval=10.0,  # 10秒间隔
        random_variance=0.3,  # 30%随机波动
        initial_delay=1.0
    )
    
    DEFAULT_LIKE_CONFIG = PushConfig(
        push_type=PushType.LIKE,
        total_duration=180,  # 3分钟
        base_interval=8.0,  # 8秒间隔
        random_variance=0.3,  # 30%随机波动
        initial_delay=0.5
    )
    
    @classmethod
    def get_comment_config(cls, 
                          total_duration: int = 300,
                          base_interval: float = 10.0) -> PushConfig:
        """获取评论推送配置"""
        return PushConfig(
            push_type=PushType.COMMENT,
            total_duration=total_duration,
            base_interval=base_interval,
            random_variance=0.3,
            initial_delay=1.0
        )
    
    @classmethod
    def get_like_config(cls,
                       total_duration: int = 180,
                       base_interval: float = 8.0) -> PushConfig:
        """获取点赞推送配置"""
        return PushConfig(
            push_type=PushType.LIKE,
            total_duration=total_duration,
            base_interval=base_interval,
            random_variance=0.3,
            initial_delay=0.5
        )

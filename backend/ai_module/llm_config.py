"""
大模型配置管理模块

统一管理所有大模型调用的参数配置，包括模型名称、温度、最大token数等。
"""

from typing import Dict, Any


class LLMConfig:
    """大模型配置类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        "model_name": "qwen-flash-2025-07-28",
        "temperature": 0.5,
        "max_tokens": 512,
        "max_retries": 3,
        "retry_delay": 1.0
    }
    
    # 评论相关任务配置
    COMMENT_CONFIG = {
        "model_name": "qwen-plus-2025-01-25",
        "temperature": 1.99,
        "max_tokens": 8192,
        "max_retries": 3,
        "retry_delay": 1.0
    }
    
    # 帖子统计预测配置
    POST_STATS_CONFIG = {
        "model_name": "qwen-flash-2025-07-28",
        "temperature": 0.1,
        "max_tokens": 256,
        "max_retries": 3,
        "retry_delay": 1.0
    }
    
    @classmethod
    def get_config(cls, config_type: str = "default") -> Dict[str, Any]:
        """
        获取指定类型的配置
        
        Args:
            config_type: 配置类型，可选值：
                - "default": 默认配置
                - "comment": 评论相关任务配置
                - "post_stats": 帖子统计预测配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        config_map = {
            "default": cls.DEFAULT_CONFIG,
            "comment": cls.COMMENT_CONFIG,
            "post_stats": cls.POST_STATS_CONFIG
        }
        
        return config_map.get(config_type, cls.DEFAULT_CONFIG)
    
    @classmethod
    def get_model_name(cls, config_type: str = "default") -> str:
        """获取模型名称"""
        return cls.get_config(config_type)["model_name"]
    
    @classmethod
    def get_temperature(cls, config_type: str = "default") -> float:
        """获取温度参数"""
        return cls.get_config(config_type)["temperature"]
    
    @classmethod
    def get_max_tokens(cls, config_type: str = "default") -> int:
        """获取最大token数"""
        return cls.get_config(config_type)["max_tokens"]
    
    @classmethod
    def get_max_retries(cls, config_type: str = "default") -> int:
        """获取最大重试次数"""
        return cls.get_config(config_type)["max_retries"]
    
    @classmethod
    def get_retry_delay(cls, config_type: str = "default") -> float:
        """获取重试延迟时间"""
        return cls.get_config(config_type)["retry_delay"]


# 便捷函数，用于快速获取配置
def get_comment_config() -> Dict[str, Any]:
    """获取评论相关任务配置"""
    return LLMConfig.get_config("comment")


def get_post_stats_config() -> Dict[str, Any]:
    """获取帖子统计预测配置"""
    return LLMConfig.get_config("post_stats")


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return LLMConfig.get_config("default")


if __name__ == "__main__":
    # 测试配置
    print("默认配置:", get_default_config())
    print("评论配置:", get_comment_config())
    print("帖子统计配置:", get_post_stats_config())

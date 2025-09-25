"""
Redis配置管理模块
本地开发环境的Redis连接配置
"""
import os
from typing import Optional

def get_redis_url() -> str:
    """
    获取Redis连接URL
    
    Returns:
        str: Redis连接URL
    """
    # 本地开发环境配置
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    redis_db = os.getenv('REDIS_DB', '0')
    redis_password = os.getenv('REDIS_PASSWORD', '')
    
    if redis_password:
        return f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
    else:
        return f"redis://{redis_host}:{redis_port}/{redis_db}"

def get_redis_config() -> dict:
    """
    获取Redis配置字典
    
    Returns:
        dict: Redis配置参数
    """
    return {
        'url': get_redis_url(),
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'connection_pool_kwargs': {
            'max_connections': 50,
            'retry_on_timeout': True,
            'socket_connect_timeout': 5,
            'socket_timeout': 5
        }
    }

def test_redis_connection() -> bool:
    """
    测试Redis连接是否正常
    
    Returns:
        bool: 连接是否成功
    """
    try:
        import redis
        r = redis.from_url(get_redis_url())
        r.ping()
        return True
    except Exception as e:
        print(f"Redis连接失败: {e}")
        return False

if __name__ == "__main__":
    print(f"Redis URL: {get_redis_url()}")
    print(f"Redis连接测试: {'成功' if test_redis_connection() else '失败'}")

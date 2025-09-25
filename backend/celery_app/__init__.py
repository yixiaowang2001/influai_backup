"""
Celery应用初始化模块
配置和创建Celery应用实例
"""
from celery import Celery
from backend.configs.redis_config import get_redis_url
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def create_celery_app() -> Celery:
    """
    创建和配置Celery应用
    
    Returns:
        Celery: 配置好的Celery应用实例
    """
    # 创建Celery应用
    celery_app = Celery(
        'influai',
        broker=get_redis_url(),
        backend=get_redis_url(),
        include=['backend.celery_app.tasks']
    )
    
    # Celery配置 - 简化版本
    celery_app.conf.update(
        # 序列化配置
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        
        # 时区配置
        timezone='Asia/Shanghai',
        enable_utc=True,
        
        # 任务配置
        task_track_started=True,
        task_time_limit=300,  # 5分钟硬超时
        task_soft_time_limit=240,  # 4分钟软超时
        
        # Worker配置
        worker_prefetch_multiplier=1,  # 防止任务堆积
        task_acks_late=True,  # 任务完成后才确认
        
        # 结果配置
        result_expires=3600,  # 结果保存1小时
        
        # 基本任务配置
        task_annotations={
            '*': {'rate_limit': '100/m'},  # 统一限制
        }
    )
    
    logger.info("Celery应用创建完成")
    logger.info(f"Broker URL: {get_redis_url()}")
    
    return celery_app

# 创建全局Celery应用实例
celery_app = create_celery_app()

# 导出给外部使用
__all__ = ['celery_app', 'create_celery_app']

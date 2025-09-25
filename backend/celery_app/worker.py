#!/usr/bin/env python3
"""
Celery Worker启动脚本
用于启动AI评论生成Worker进程
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from backend.celery_app import celery_app
from backend.utils.logger import get_logger
from backend.configs.redis_config import test_redis_connection

logger = get_logger(__name__)

def main():
    """启动Celery Worker"""
    
    # 检查Redis连接
    logger.info("检查Redis连接...")
    if not test_redis_connection():
        logger.error("Redis连接失败，请确保Redis服务已启动")
        logger.error("启动Redis服务: redis-server")
        sys.exit(1)
    
    logger.info("Redis连接正常")
    
    # 启动Worker
    logger.info("启动Celery Worker...")
    logger.info("Worker配置:")
    logger.info(f"  - 并发数: 2")
    logger.info(f"  - 日志级别: info")
    logger.info(f"  - 队列: ai_comments, health")
    
    # 启动Celery Worker - 简化版本
    # 参数说明:
    # --loglevel=info: 设置日志级别
    # --concurrency=2: 设置并发worker数量（本地环境使用2个足够）
    # --hostname=influai_worker: 设置worker主机名（添加时间戳避免冲突）
    import time
    hostname = f"influai_worker_{int(time.time())}@%h"
    
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--hostname=' + hostname
    ])

if __name__ == '__main__':
    main()

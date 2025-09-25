#!/usr/bin/env python3
"""
InfluAI Flower 监控启动脚本
用于启动Celery任务监控界面
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from backend.celery_app import celery_app
from backend.configs.redis_config import test_redis_connection, get_redis_url
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """启动Flower监控"""
    
    print("=" * 60)
    print("InfluAI Flower 监控启动中...")
    print("=" * 60)
    print()
    
    # 检查Redis连接
    logger.info("检查Redis连接...")
    if not test_redis_connection():
        logger.error("Redis连接失败，请确保Redis服务已启动")
        logger.info("启动命令: redis-server")
        sys.exit(1)
    
    logger.info("Redis连接正常")
    print()
    
    # 启动Flower
    logger.info("启动Flower监控界面...")
    logger.info(f"监控地址: http://localhost:5555")
    logger.info(f"Redis URL: {get_redis_url()}")
    print()
    print("=" * 60)
    
    # 启动Flower
    # 参数说明:
    # --port=5555: 设置Flower Web界面端口
    # --broker: 指定broker URL
    celery_app.control.purge()  # 清理已完成的任务
    
    os.system(f"celery -A backend.celery_app flower --port=5555 --broker={get_redis_url()}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭Flower...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Flower启动失败: {e}")
        sys.exit(1)

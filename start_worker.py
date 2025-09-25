#!/usr/bin/env python3
"""
InfluAI Celery Worker 启动脚本
用于本地开发环境启动AI评论生成Worker
"""
import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from backend.celery_app.worker import main

if __name__ == '__main__':
    print("=" * 60)
    print("InfluAI Celery Worker 启动中...")
    print("=" * 60)
    print()
    print("启动步骤:")
    print("1. 检查Redis连接")
    print("2. 初始化Celery应用")
    print("3. 启动Worker进程")
    print()
    print("请确保Redis服务已启动:")
    print("   redis-server")
    print()
    print("Worker配置:")
    print("   - 并发数: 2")
    print("   - 队列: ai_comments, health") 
    print("   - 日志级别: info")
    print()
    print("=" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭Worker...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker启动失败: {e}")
        sys.exit(1)

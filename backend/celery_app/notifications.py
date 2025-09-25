"""
通知模块
处理Celery任务完成后的通知逻辑
"""
import json
import asyncio
from datetime import datetime
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def notify_comments_ready(post_id: int, task_id: str = None):
    """
    通知主服务评论生成完毕，可以开始推送
    
    Args:
        post_id: 帖子ID
        task_id: 任务ID（可选）
    """
    try:
        # 由于这是在Celery Worker进程中运行，我们不能直接调用主服务的WebSocket
        # 这里我们记录日志，主服务的评论推送任务会自动检测到新评论并开始推送
        logger.info(f"评论生成完成通知: post_id={post_id}, task_id={task_id}")
        logger.info("主服务的评论推送任务将自动检测到新评论并开始推送")
        
        # 可选：如果需要更复杂的通知机制，可以：
        # 1. 通过Redis发布消息
        # 2. 写入数据库状态表
        # 3. 调用主服务的HTTP API
        
        # 示例：通过Redis发布通知消息
        try:
            import redis
            from backend.configs.redis_config import get_redis_url
            
            r = redis.from_url(get_redis_url())
            notification = {
                'type': 'comments_ready',
                'post_id': post_id,
                'task_id': task_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # 发布到Redis频道，主服务可以订阅此频道
            r.publish('influai_notifications', json.dumps(notification))
            logger.info(f"已发布评论就绪通知到Redis: {notification}")
            
        except Exception as e:
            logger.warning(f"发布Redis通知失败: {e}")
            
    except Exception as e:
        logger.error(f"发送评论就绪通知失败: {e}")

def notify_task_progress(task_id: str, progress: int, stage: str, post_id: int):
    """
    通知任务进度更新
    
    Args:
        task_id: 任务ID
        progress: 进度百分比
        stage: 当前阶段
        post_id: 帖子ID
    """
    try:
        import redis
        from backend.configs.redis_config import get_redis_url
        
        r = redis.from_url(get_redis_url())
        progress_info = {
            'type': 'task_progress',
            'task_id': task_id,
            'progress': progress,
            'stage': stage,
            'post_id': post_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # 发布进度更新
        r.publish('influai_task_progress', json.dumps(progress_info))
        logger.debug(f"任务进度通知: {progress_info}")
        
    except Exception as e:
        logger.warning(f"发送任务进度通知失败: {e}")

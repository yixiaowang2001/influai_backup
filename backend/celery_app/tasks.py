"""
Celery任务定义模块
定义AI评论生成等异步任务
"""
from datetime import datetime
from celery import current_task
from backend.celery_app import celery_app
from backend.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, name='generate_comments_task')
def generate_comments_task(self, post_id: int, human_user_id: int, template_id: int):
    """
    AI评论生成任务 - 在独立进程中运行
    
    Args:
        self: Celery任务实例
        post_id: 帖子ID
        human_user_id: 人类用户ID  
        template_id: 用户模板ID
        
    Returns:
        dict: 任务执行结果
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] 开始AI评论生成任务")
    logger.info(f"[Task {task_id}] 参数: post_id={post_id}, human_user_id={human_user_id}, template_id={template_id}")
    
    # 更新任务状态为进行中
    self.update_state(
        state='PROGRESS',
        meta={
            'progress': 0, 
            'stage': 'initializing', 
            'post_id': post_id,
            'start_time': datetime.now().isoformat()
        }
    )
    
    # 创建独立的数据库会话，避免与主服务的数据库连接竞争
    from backend.database.database import get_db_session
    db = get_db_session()
    
    try:
        # 第一步：验证帖子存在
        self.update_state(
            state='PROGRESS',
            meta={'progress': 5, 'stage': 'validating_post', 'post_id': post_id}
        )
        
        from backend.database import models
        post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
        if not post:
            raise ValueError(f"未找到帖子ID: {post_id}")
        
        logger.info(f"[Task {task_id}] 找到帖子: {post.post_content[:50]}...")
        
        # 第二步：验证用户和模板
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'stage': 'validating_user', 'post_id': post_id}
        )
        
        from backend.database import crud
        human_user = crud.get_human_user_by_id(db, human_user_id)
        if not human_user:
            raise ValueError(f"未找到人类用户ID: {human_user_id}")
        
        template = crud.get_user_template_by_id(db, template_id)
        if not template:
            raise ValueError(f"未找到模板ID: {template_id}")
        
        logger.info(f"[Task {task_id}] 用户验证完成: {human_user.username}")
        
        # 第三步：初始化PostService
        self.update_state(
            state='PROGRESS',
            meta={'progress': 15, 'stage': 'creating_service', 'post_id': post_id}
        )
        
        from backend.services.post_service import PostService
        post_service = PostService(
            content=post.post_content,
            template_id=template_id,
            human_user_id=human_user_id,
            db=db
        )
        
        logger.info(f"[Task {task_id}] PostService初始化完成")
        
        # 第四步：执行basic_update（预计耗时27秒）
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'stage': 'basic_update', 'post_id': post_id}
        )
        
        logger.info(f"[Task {task_id}] 开始执行basic_update...")
        post_service.basic_update()
        logger.info(f"[Task {task_id}] basic_update完成")
        
        # 第五步：开始生成评论（预计耗时80+秒）
        self.update_state(
            state='PROGRESS',
            meta={'progress': 40, 'stage': 'generating_comments', 'post_id': post_id}
        )
        
        logger.info(f"[Task {task_id}] 开始生成{post_service.pred_comment_count}条评论...")
        
        # 分态度生成评论，每完成一种态度更新一次进度
        from backend.models import Attitude
        comment_nums_by_attitude = post_service.distribute_comment_nums(total=post_service.pred_comment_count)
        total_attitudes = len(Attitude.create_dict().keys())
        completed_attitudes = 0
        
        for att in Attitude.create_dict().keys():
            comment_count = comment_nums_by_attitude[str(att)]
            logger.info(f"[Task {task_id}] 生成{att}态度评论: {comment_count}条")
            
            expanded_comments = post_service.expand_lv1_comments_by_attitude(att, comment_count)
            for comment in expanded_comments:
                comment.post_id = post_id
                ai_user_id = post_service.assign_ai_user_to_comment(comment, att)
                if ai_user_id:
                    comment.sender_id = ai_user_id
                post_service.comments.append(comment)
                crud.create_comment(db, comment)
            
            # 更新进度
            completed_attitudes += 1
            progress = 40 + int(50 * completed_attitudes / total_attitudes)
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress, 
                    'stage': f'generated_{att}_comments', 
                    'post_id': post_id,
                    'completed_attitudes': completed_attitudes,
                    'total_attitudes': total_attitudes
                }
            )
            
            logger.info(f"[Task {task_id}] {att}态度评论生成完成: {len(expanded_comments)}条")
        
        # 第六步：更新帖子统计
        self.update_state(
            state='PROGRESS',
            meta={'progress': 95, 'stage': 'updating_post_stats', 'post_id': post_id}
        )
        
        # 构建统计数据
        stats = {
            "pred_like_count": post_service.post.like_count,
            "pred_comment_count": post_service.pred_comment_count,
            "new_follower_count": post_service.new_follower_count
        }
        
        # 更新帖子的统计数据
        post.like_count = stats["pred_like_count"]
        db.commit()
        
        # 生成AI用户点赞记录
        logger.info(f"[Task {task_id}] 开始生成点赞记录，预测点赞数: {stats['pred_like_count']}")
        
        # 获取该人类用户的所有AI用户，优先选择态度值较高的用户
        from backend.database.db_utils import get_available_ai_users_by_attitude
        from backend.models.attitude import Attitude
        
        # 获取所有态度的AI用户
        all_ai_users = []
        for attitude in Attitude.create_dict().keys():
            attitude_users = get_available_ai_users_by_attitude(
                db=db,
                attitude_type=attitude,
                human_user_id=human_user_id
            )
            all_ai_users.extend(attitude_users)
        
        # 按态度值排序，优先选择态度值较高的用户
        all_ai_users.sort(key=lambda user: abs(user.attitude_value), reverse=True)
        
        # 生成点赞记录
        import random
        like_count = stats["pred_like_count"]
        created_likes = 0
        
        for i in range(like_count):
            if not all_ai_users:
                logger.warning(f"[Task {task_id}] 没有可用的AI用户生成点赞记录")
                break
            
            # 随机选择一个AI用户（优先选择态度值高的用户）
            # 使用加权随机选择，态度值高的用户权重更高
            weights = [abs(user.attitude_value) + 0.1 for user in all_ai_users]  # 加0.1避免权重为0
            selected_user = random.choices(all_ai_users, weights=weights, k=1)[0]
            
            # 创建点赞记录
            from backend.database import crud
            crud.create_post_like(
                db=db,
                post_id=post_id,
                liker_id=selected_user.user_id,
                liker_type="ai_user"
            )
            created_likes += 1
            
            logger.debug(f"[Task {task_id}] 创建点赞记录: AI用户 {selected_user.username} 点赞帖子 {post_id}")
        
        logger.info(f"[Task {task_id}] 点赞记录生成完成: {created_likes} 条")
        
        logger.info(f"[Task {task_id}] 统计数据更新完成")
        
        # 第七步：任务完成
        result = {
            'post_id': post_id,
            'comment_count': len(post_service.comments),
            'stats': stats,
            'task_id': task_id,
            'completion_time': datetime.now().isoformat()
        }
        
        self.update_state(
            state='SUCCESS',
            meta={
                'progress': 100, 
                'stage': 'completed', 
                'post_id': post_id,
                'result': result
            }
        )
        
        logger.info(f"[Task {task_id}] AI评论生成任务完成")
        logger.info(f"[Task {task_id}] 生成评论数: {len(post_service.comments)}")
        logger.info(f"[Task {task_id}] 预测点赞数: {stats['pred_like_count']}")
        logger.info(f"[Task {task_id}] 预测评论数: {stats['pred_comment_count']}")
        
        # 通知主服务评论已生成完毕，可以开始推送
        try:
            from backend.celery_app.notifications import notify_comments_ready
            notify_comments_ready(post_id, task_id)
        except Exception as e:
            logger.warning(f"[Task {task_id}] 通知评论就绪失败: {e}")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Task {task_id}] AI评论生成失败: {error_msg}")
        
        # 更新任务状态为失败
        self.update_state(
            state='FAILURE',
            meta={
                'progress': 0, 
                'stage': 'failed', 
                'post_id': post_id, 
                'error': error_msg,
                'failure_time': datetime.now().isoformat()
            }
        )
        
        # 重新抛出异常，让Celery处理
        raise
        
    finally:
        # 确保数据库会话被正确关闭
        try:
            db.close()
            logger.info(f"[Task {task_id}] 数据库会话已关闭")
        except Exception as e:
            logger.error(f"[Task {task_id}] 关闭数据库会话失败: {e}")

@celery_app.task(name='health_check_task')
def health_check_task():
    """
    健康检查任务
    
    Returns:
        dict: 健康状态信息
    """
    logger.info("执行健康检查任务")
    
    try:
        # 检查数据库连接
        from backend.database.database import get_db_session
        db = get_db_session()
        
        try:
            # 简单查询测试数据库连接
            from backend.database import models
            post_count = db.query(models.Post).count()
            db.close()
            
            result = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'post_count': post_count
            }
            
            logger.info("健康检查通过")
            return result
            
        except Exception as e:
            db.close()
            raise e
            
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }

@celery_app.task(name='test_task')
def test_task(message: str = "Hello from Celery!"):
    """
    测试任务
    
    Args:
        message: 测试消息
        
    Returns:
        dict: 测试结果
    """
    logger.info(f"执行测试任务: {message}")
    
    import time
    time.sleep(2)  # 模拟一些工作
    
    return {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'status': 'completed'
    }

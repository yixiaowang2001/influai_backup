"""
通用推送服务
支持固定时间、固定间隔（+30%随机波动）的批量推送逻辑
"""
import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from backend.utils.logger import get_logger

logger = get_logger(__name__)
from backend.services.push_config import PushConfig, PushType


@dataclass
class PushItem:
    """推送项目"""
    id: str
    content: Any
    metadata: Dict[str, Any]


class GenericPushManager:
    """通用推送管理器"""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.active_tasks = {}  # 存储活跃的推送任务
        
    async def start_push_task(self, 
                            target_id: str, 
                            config: PushConfig, 
                            get_items_func: Callable,
                            format_message_func: Callable,
                            update_status_func: Optional[Callable] = None) -> str:
        """
        启动推送任务
        
        Args:
            target_id: 目标ID（如帖子ID）
            config: 推送配置
            get_items_func: 获取待推送项目的函数
            format_message_func: 格式化推送消息的函数
            update_status_func: 更新推送状态的函数（可选）
        
        Returns:
            任务ID
        """
        task_id = f"{config.push_type.value}_{target_id}_{datetime.now().timestamp()}"
        
        if task_id in self.active_tasks:
            logger.warning(f"推送任务 {task_id} 已存在")
            return task_id
        
        # 创建推送任务
        task = asyncio.create_task(
            self._execute_push_task(
                task_id, target_id, config, 
                get_items_func, format_message_func, update_status_func
            )
        )
        self.active_tasks[task_id] = task
        
        logger.info(f"启动推送任务 {task_id} - 类型: {config.push_type.value}, 目标: {target_id}")
        return task_id
    
    async def _execute_push_task(self, 
                               task_id: str,
                               target_id: str, 
                               config: PushConfig,
                               get_items_func: Callable,
                               format_message_func: Callable,
                               update_status_func: Optional[Callable] = None):
        """执行推送任务的核心逻辑"""
        try:
            logger.info(f"开始执行推送任务 {task_id}")
            
            # 初始延迟
            await asyncio.sleep(config.initial_delay)
            
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=config.total_duration)
            push_count = 0
            
            # 获取所有待推送的项目
            all_items = get_items_func(target_id)
            if not all_items:
                logger.info(f"没有待推送项目，任务 {task_id} 结束")
                return
            
            total_items = len(all_items)
            logger.info(f"总共有 {total_items} 个项目需要推送")
            
            # 计算推送轮次和每轮推送数量
            total_push_rounds = int(config.total_duration / config.base_interval)
            base_items_per_round = max(1, total_items // total_push_rounds) if total_push_rounds > 0 else total_items
            
            logger.info(f"预计推送轮次: {total_push_rounds}, 基础每轮推送: {base_items_per_round} 个项目")
            
            current_round = 0
            remaining_items = total_items
            
            while datetime.now() < end_time and current_round < total_push_rounds and remaining_items > 0:
                # 计算本轮推送数量（添加随机波动）
                if current_round == total_push_rounds - 1:
                    # 最后一轮：推送所有剩余评论
                    items_to_push_count = remaining_items
                else:
                    # 前N-1轮：基础数量 + 随机波动
                    # 波动范围：基础数量的 ±50%
                    variance_range = base_items_per_round * 0.5
                    variance = random.uniform(-variance_range, variance_range)
                    items_to_push_count = max(1, int(base_items_per_round + variance))
                    
                    # 确保不超过剩余数量
                    items_to_push_count = min(items_to_push_count, remaining_items)
                
                # 获取本轮要推送的项目
                start_idx = total_items - remaining_items
                end_idx = start_idx + items_to_push_count
                items_to_push = all_items[start_idx:end_idx]
                
                if not items_to_push:
                    logger.info(f"没有更多待推送项目，任务 {task_id} 提前结束")
                    break
                
                # 推送本轮项目
                for item in items_to_push:
                    message = format_message_func(target_id, item)
                    await self.connection_manager.broadcast(json.dumps(message))
                    
                    # 更新推送状态
                    if update_status_func:
                        update_status_func(item.id)
                    
                    push_count += 1
                    logger.info(f"推送 {config.push_type.value} - 目标: {target_id}, 项目ID: {item.id}")
                
                remaining_items -= items_to_push_count
                current_round += 1
                
                logger.info(f"第{current_round}轮推送完成: {items_to_push_count}个项目, 剩余{remaining_items}个")
                
                # 如果已经推送完所有项目，提前结束
                if remaining_items <= 0:
                    logger.info(f"所有项目已推送完毕，任务 {task_id} 提前结束")
                    break
                
                # 计算下次推送的等待时间（基础间隔 + 随机波动）
                variance = config.base_interval * config.random_variance
                wait_time = config.base_interval + random.uniform(-variance, variance)
                
                # 确保等待时间不为负数
                wait_time = max(0.1, wait_time)
                
                logger.info(f"等待 {wait_time:.2f} 秒后进行下一轮推送")
                await asyncio.sleep(wait_time)
            
            # 发送完成通知
            completion_message = {
                "type": f"{config.push_type.value}_push_complete",
                "data": {
                    "targetId": target_id,
                    "message": f"该目标的{config.push_type.value}推送已完毕",
                    "totalPushed": push_count
                }
            }
            await self.connection_manager.broadcast(json.dumps(completion_message))
            
            logger.info(f"推送任务 {task_id} 完成 - 总推送数: {push_count}")
            
        except Exception as e:
            logger.error(f"推送任务 {task_id} 执行失败: {e}")
        finally:
            # 清理任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def stop_push_task(self, task_id: str) -> bool:
        """停止指定的推送任务"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
            logger.info(f"已停止推送任务 {task_id}")
            return True
        return False
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """获取所有活跃任务的信息"""
        return {
            task_id: {
                "status": "running",
                "type": task_id.split('_')[0]
            }
            for task_id in self.active_tasks.keys()
        }


class CommentPushService:
    """评论推送服务"""
    
    def __init__(self, push_manager: GenericPushManager, db_session_func):
        self.push_manager = push_manager
        self.db_session_func = db_session_func
    
    def get_unpushed_comments(self, post_id: str) -> List[PushItem]:
        """获取未推送的评论"""
        from backend.database import crud
        
        db = self.db_session_func()
        try:
            comments = crud.get_comments_by_post(db, int(post_id))
            unprocessed_comments = [c for c in comments if not c.send_at]
            
            push_items = []
            for comment in unprocessed_comments:
                # 获取评论者信息
                author_info = self._get_author_info(db, comment)
                
                push_item = PushItem(
                    id=str(comment.comment_id),
                    content={
                        "id": f"comment_{comment.comment_id}",
                        "content": comment.comment_content,
                        "author": author_info,
                        "timestamp": self._format_timestamp(comment.created_at),
                        "createdAt": comment.created_at.isoformat(),
                        "likes": comment.comment_likes,
                        "isLiked": comment.is_human_user_liked == 1
                    },
                    metadata={
                        "comment_id": comment.comment_id,
                        "sender_type": comment.sender_type,
                        "sender_id": comment.sender_id
                    }
                )
                push_items.append(push_item)
            
            return push_items
            
        finally:
            db.close()
    
    def format_comment_message(self, post_id: str, item: PushItem) -> Dict[str, Any]:
        """格式化评论推送消息"""
        return {
            "type": "new_comment_push",
            "data": {
                "postId": f"post_{post_id}",
                "comment": item.content
            }
        }
    
    def update_comment_push_status(self, comment_id: str):
        """更新评论推送状态"""
        from backend.database import crud
        
        db = self.db_session_func()
        try:
            comment = db.query(crud.models.Comment).filter(
                crud.models.Comment.comment_id == int(comment_id)
            ).first()
            if comment:
                comment.send_at = datetime.now()
                db.commit()
        finally:
            db.close()
    
    def _get_author_info(self, db, comment):
        """获取评论者信息"""
        from backend.database import crud
        
        author_info = {}
        if comment.sender_type == "ai_user":
            ai_user = crud.get_ai_user(db, comment.sender_id)
            if ai_user:
                author_info = {
                    "id": ai_user.user_id,
                    "username": ai_user.username,
                    "userId": f"@{ai_user.username.lower()}"
                }
        elif comment.sender_type == "human_user":
            human_user = crud.get_human_user_by_id(db, int(comment.sender_id))
            if human_user:
                author_info = {
                    "id": f"human_{human_user.user_id}",
                    "username": human_user.username,
                    "userId": f"@{human_user.username.lower()}"
                }
        return author_info
    
    def _format_timestamp(self, created_at: datetime) -> str:
        """格式化时间戳"""
        now = datetime.now()
        diff = now - created_at
        
        if diff.total_seconds() < 60:
            return "刚刚"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}分钟前"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}小时前"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days}天前"


class LikePushService:
    """点赞推送服务"""
    
    def __init__(self, push_manager: GenericPushManager, db_session_func):
        self.push_manager = push_manager
        self.db_session_func = db_session_func
    
    def get_unpushed_likes(self, target_id: str) -> List[PushItem]:
        """获取待推送的点赞（这里需要根据实际业务逻辑实现）"""
        # 这里需要根据你的点赞业务逻辑来实现
        # 例如：获取某个帖子或评论的待推送点赞
        return []
    
    def format_like_message(self, target_id: str, item: PushItem) -> Dict[str, Any]:
        """格式化点赞推送消息"""
        return {
            "type": "like_push",
            "data": {
                "targetId": target_id,
                "likeData": item.content
            }
        }
    
    def update_like_push_status(self, like_id: str):
        """更新点赞推送状态"""
        # 根据实际业务逻辑实现
        pass

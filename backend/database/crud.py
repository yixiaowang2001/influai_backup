from typing import List, Optional

from sqlalchemy.orm import Session

import backend.database.models as models
from backend.database.models import Post as PostModel, Comment as CommentModel, AIUser as AIUserModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_post(db: Session, post: PostModel) -> models.Post:
    """
    创建新帖子
    
    Args:
        db: 数据库会话
        post: 帖子模型对象
        
    Returns:
        models.Post: 创建的帖子对象
    """
    logger.debug(f"开始创建帖子，内容长度: {len(post.post_content)}")
    db_post = models.Post(
        post_content=post.post_content,
        author_id=post.author_id,
        like_count=post.like_count or 0,
        created_at=post.created_at
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    logger.info(f"成功创建帖子，ID: {db_post.post_id}")
    return db_post


def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[models.Post]:
    """
    获取帖子列表
    
    Args:
        db: 数据库会话
        skip: 跳过的记录数
        limit: 限制返回的记录数
        
    Returns:
        List[models.Post]: 帖子列表
    """
    return db.query(models.Post).offset(skip).limit(limit).all()


def get_latest_n_posts(db: Session, n: int) -> List[models.Post]:
    """
    获取最新的n个帖子，按created_at字段降序排列
    
    Args:
        db: 数据库会话
        n: 要获取的帖子数量
        
    Returns:
        List[models.Post]: 最新的n个帖子列表
    """
    return db.query(models.Post).order_by(models.Post.created_at.desc()).limit(n).all()


def create_ai_user(db: Session, ai_user: AIUserModel) -> models.AIUser:
    """
    创建AI用户
    
    Args:
        db: 数据库会话
        ai_user: AI用户模型对象
        
    Returns:
        models.AIUser: 创建的AI用户对象
    """
    logger.debug(f"开始创建AI用户，用户名: {ai_user.username}")
    db_ai_user = models.AIUser(
        username=ai_user.username,
        avatar_path=ai_user.avatar_path,
        attitude_value=ai_user.attitude_value,
        created_at=ai_user.created_at
    )
    db.add(db_ai_user)
    db.commit()
    db.refresh(db_ai_user)
    logger.info(f"成功创建AI用户，ID: {db_ai_user.user_id}，用户名: {db_ai_user.username}")
    return db_ai_user


def get_ai_user(db: Session, user_id: str) -> Optional[models.AIUser]:
    """
    根据用户ID获取AI用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID（字符串类型）
        
    Returns:
        Optional[models.AIUser]: AI用户对象，如果不存在则返回None
    """
    return db.query(models.AIUser).filter(models.AIUser.user_id == user_id).first()


def create_comment(db: Session, comment: CommentModel) -> models.Comment:
    """
    创建评论
    
    Args:
        db: 数据库会话
        comment: 评论模型对象
        
    Returns:
        models.Comment: 创建的评论对象
    """
    logger.debug(f"开始创建评论，内容长度: {len(comment.comment_content)}，态度: {comment.comment_attitude}")
    db_comment = models.Comment(
        comment_content=comment.comment_content,
        comment_user_type=comment.comment_user_type,
        comment_level=comment.comment_level,
        comment_likes=comment.comment_likes,
        master_comment_id=comment.master_comment_id,
        created_at=comment.created_at,
        send_at=comment.send_at,
        post_id=comment.post_id,
        ai_user_id=comment.comment_user_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    logger.info(f"成功创建评论，ID: {db_comment.comment_id}，帖子ID: {db_comment.post_id}")
    return db_comment


def get_comments_by_post(db: Session, post_id: int) -> List[models.Comment]:
    """
    根据帖子ID获取评论列表
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        
    Returns:
        List[models.Comment]: 评论列表
    """
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()


def get_all_ai_users(db: Session) -> List[models.AIUser]:
    """
    获取所有AI用户
    
    Args:
        db: 数据库会话
        
    Returns:
        List[models.AIUser]: AI用户列表
    """
    return db.query(models.AIUser).all()


def get_ai_users_by_attitude(db: Session, attitude_type) -> List[models.AIUser]:
    """
    根据态度类型获取AI用户列表
    
    Args:
        db: 数据库会话
        attitude_type: 态度类型枚举
        
    Returns:
        List[models.AIUser]: 符合态度类型的AI用户列表
    """
    lower_bound, upper_bound = attitude_type.value
    return db.query(models.AIUser).filter(
        models.AIUser.attitude_value >= lower_bound,
        models.AIUser.attitude_value < upper_bound
    ).all()


def get_available_ai_users_by_attitude(db: Session, attitude_type, exclude_user_ids: List[str] = None) -> List[
    models.AIUser]:
    """
    根据态度类型获取可用的AI用户列表（排除已分配的用户）
    
    Args:
        db: 数据库会话
        attitude_type: 态度类型枚举
        exclude_user_ids: 要排除的用户ID列表
        
    Returns:
        List[models.AIUser]: 可用的AI用户列表
    """
    lower_bound, upper_bound = attitude_type.value
    query = db.query(models.AIUser).filter(
        models.AIUser.attitude_value >= lower_bound,
        models.AIUser.attitude_value < upper_bound
    )
    
    if exclude_user_ids:
        query = query.filter(~models.AIUser.user_id.in_(exclude_user_ids))
    
    return query.all()


def get_user_template_by_name(db: Session, template_name: str) -> Optional[models.UserTemplate]:
    """
    根据模板名称获取用户模板
    
    Args:
        db: 数据库会话
        template_name: 模板名称
        
    Returns:
        Optional[models.UserTemplate]: 用户模板对象，如果不存在则返回None
    """
    return db.query(models.UserTemplate).filter(models.UserTemplate.template_name == template_name).first()


def get_all_user_templates(db: Session) -> List[models.UserTemplate]:
    """
    获取所有用户模板
    
    Args:
        db: 数据库会话
        
    Returns:
        List[models.UserTemplate]: 所有用户模板列表
    """
    return db.query(models.UserTemplate).all()


def get_human_user_by_id(db: Session, user_id: int) -> Optional[models.HumanUser]:
    """
    根据用户ID获取人类用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Optional[models.HumanUser]: 人类用户对象，如果不存在则返回None
    """
    return db.query(models.HumanUser).filter(models.HumanUser.user_id == user_id).first()


def get_first_human_user(db: Session) -> Optional[models.HumanUser]:
    """
    获取第一个人类用户（用于默认用户）
    
    Args:
        db: 数据库会话
        
    Returns:
        Optional[models.HumanUser]: 第一个人类用户对象，如果不存在则返回None
    """
    return db.query(models.HumanUser).first()


def get_all_human_users(db: Session) -> List[models.HumanUser]:
    """
    获取所有人类用户
    
    Args:
        db: 数据库会话
        
    Returns:
        List[models.HumanUser]: 所有人类用户列表
    """
    return db.query(models.HumanUser).all()

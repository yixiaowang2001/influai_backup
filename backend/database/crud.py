from typing import List, Optional

from sqlalchemy.orm import Session

import backend.database.models as models
from backend.database.models import Post as PostModel, Comment as CommentModel, AIUser as AIUserModel


def create_post(db: Session, post: PostModel) -> models.Post:
    db_post = models.Post(
        post_content=post.post_content,
        like_count=post.like_count or 0,
        created_at=post.created_at
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


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
    db_ai_user = models.AIUser(
        username=ai_user.username,
        avatar_path=ai_user.avatar_path,
        attitude_value=ai_user.attitude_value,
        created_at=ai_user.created_at
    )
    db.add(db_ai_user)
    db.commit()
    db.refresh(db_ai_user)
    return db_ai_user


def get_ai_user(db: Session, user_id: int) -> Optional[models.AIUser]:
    return db.query(models.AIUser).filter(models.AIUser.user_id == user_id).first()


def create_comment(db: Session, comment: CommentModel) -> models.Comment:
    db_comment = models.Comment(
        comment_content=comment.comment_content,
        comment_user_type=comment.comment_user_type,
        comment_level=comment.comment_level,
        comment_likes=comment.comment_likes,
        master_comment_id=comment.master_comment_id,
        created_at=comment.created_at,
        send_at=comment.send_at,
        post_id=comment.post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments_by_post(db: Session, post_id: int) -> List[models.Comment]:
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()

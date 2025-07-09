from sqlalchemy.orm import Session
import backend.database.models as models
from backend.database.models import Post as PostModel, Comment as CommentModel, AIUser as AIUserModel
from typing import List, Optional


def create_post(db: Session, post: PostModel) -> models.Post:
    """创建新帖子"""
    db_post = models.Post(
        post_content=post.post_content,
        like_count=post.like_count or 0,
        created_at=post.created_at
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_post(db: Session, post_id: int) -> Optional[models.Post]:
    """根据ID获取帖子"""
    return db.query(models.Post).filter(models.Post.post_id == post_id).first()


def get_posts(db: Session, skip: int = 0, limit: int = 100) -> List[models.Post]:
    """获取帖子列表"""
    return db.query(models.Post).offset(skip).limit(limit).all()


def create_ai_user(db: Session, ai_user: AIUserModel) -> models.AIUser:
    """创建AI用户"""
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
    """根据ID获取AI用户"""
    return db.query(models.AIUser).filter(models.AIUser.user_id == user_id).first()


def create_comment(db: Session, comment: CommentModel, post_id: int, ai_user_id: int = None) -> models.Comment:
    """创建评论"""
    db_comment = models.Comment(
        comment_content=comment.comment_content,
        comment_user_type=comment.comment_user_type,
        comment_attitude=str(comment.comment_attitude),
        comment_level=comment.comment_level,
        comment_likes=comment.comment_likes,
        master_comment_id=comment.master_comment_id,
        created_at=comment.created_at,
        send_at=comment.send_at,
        post_id=post_id,
        ai_user_id=ai_user_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments_by_post(db: Session, post_id: int) -> List[models.Comment]:
    """获取某帖子的所有评论"""
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
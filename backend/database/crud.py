from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from . import models
from .models import Post as PostModel, Comment as CommentModel, AIUser as AIUserModel
from ..utils.logger import get_logger

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
        is_human_user_liked=getattr(post, 'is_human_user_liked', 0),  # 获取点赞状态，默认为0
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
    logger.debug(f"开始创建评论，内容长度: {len(comment.comment_content)}")
    
    # 确定sender_type和sender_id
    if hasattr(comment, 'sender_type') and comment.sender_type:
        # 如果评论对象已经有sender_type，直接使用
        sender_type = comment.sender_type
        sender_id = comment.sender_id
    elif comment.comment_user_id:
        # 如果是AI用户评论（兼容旧版本）
        sender_type = "ai_user"
        sender_id = comment.comment_user_id
    else:
        # 如果是人类用户评论（这种情况不应该发生，因为AI评论必须有sender_id）
        sender_type = "human_user"
        sender_id = str(comment.post_id)  # 临时使用post_id，实际应该从其他地方获取
    
    db_comment = models.Comment(
        comment_content=comment.comment_content,
        comment_user_type=comment.comment_user_type,
        comment_level=comment.comment_level,
        comment_likes=comment.comment_likes,
        is_human_user_liked=getattr(comment, 'is_human_user_liked', 0),  # 获取点赞状态，默认为0
        master_comment_id=comment.master_comment_id,
        created_at=comment.created_at,
        send_at=comment.send_at,
        post_id=comment.post_id,
        sender_id=sender_id,
        sender_type=sender_type
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    logger.info(f"成功创建评论，ID: {db_comment.comment_id}，帖子ID: {db_comment.post_id}，发送者类型: {sender_type}")
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
        attitude_type: 态度类型枚举，如果为None则获取所有AI用户
        exclude_user_ids: 要排除的用户ID列表
        
    Returns:
        List[models.AIUser]: 可用的AI用户列表
    """
    if attitude_type is None:
        # 如果态度类型为None，获取所有AI用户
        query = db.query(models.AIUser)
    else:
        # 按态度类型过滤
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


def get_user_template_by_id(db: Session, template_id: int) -> Optional[models.UserTemplate]:
    """
    根据模板ID获取用户模板
    
    Args:
        db: 数据库会话
        template_id: 模板ID
        
    Returns:
        Optional[models.UserTemplate]: 用户模板对象，如果不存在则返回None
    """
    return db.query(models.UserTemplate).filter(models.UserTemplate.template_id == template_id).first()


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





def get_all_human_users(db: Session) -> List[models.HumanUser]:
    """
    获取所有人类用户
    
    Args:
        db: 数据库会话
        
    Returns:
        List[models.HumanUser]: 所有人类用户列表
    """
    return db.query(models.HumanUser).all()


def get_ai_users_by_human_user_id(db: Session, human_user_id: int) -> List[models.AIUser]:
    """
    根据人类用户ID获取所有AI用户
    
    Args:
        db: 数据库会话
        human_user_id: 人类用户ID
        
    Returns:
        List[models.AIUser]: AI用户列表
    """
    return db.query(models.AIUser).filter(models.AIUser.human_user_id == human_user_id).all()


def get_human_user_by_id_for_ai_init(db: Session, user_id: int) -> Optional[models.HumanUser]:
    """
    根据用户ID获取人类用户，用于AI用户初始化
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Optional[models.HumanUser]: 人类用户对象，如果不存在则返回None
    """
    return db.query(models.HumanUser).filter(models.HumanUser.user_id == user_id).first()


def create_comment_with_sender(db: Session, comment_content: str, post_id: int, sender_id: str, sender_type: str, comment_user_type: int = 1, comment_level: int = 1) -> models.Comment:
    """
    创建评论（支持AI用户和人类用户）
    
    Args:
        db: 数据库会话
        comment_content: 评论内容
        post_id: 帖子ID
        sender_id: 发送者ID（AI用户ID或人类用户ID）
        sender_type: 发送者类型（'ai_user' 或 'human_user'）
        comment_user_type: 评论用户类型
        comment_level: 评论级别
        
    Returns:
        models.Comment: 创建的评论对象
    """
    logger.debug(f"开始创建评论，发送者类型: {sender_type}, 发送者ID: {sender_id}")
    db_comment = models.Comment(
        comment_content=comment_content,
        comment_user_type=comment_user_type,
        comment_level=comment_level,
        comment_likes=0,
        is_human_user_liked=0,  # 新评论默认未点赞
        master_comment_id=None,
        created_at=datetime.now(),
        send_at=datetime.now(),
        post_id=post_id,
        sender_id=sender_id,
        sender_type=sender_type
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    logger.info(f"成功创建评论，ID: {db_comment.comment_id}, 发送者类型: {sender_type}")
    return db_comment


def update_post_like_status(db: Session, post_id: int, is_liked: bool) -> Optional[models.Post]:
    """
    更新帖子的点赞状态
    
    Args:
        db: 数据库会话
        post_id: 帖子ID
        is_liked: 是否已点赞
        
    Returns:
        Optional[models.Post]: 更新后的帖子对象，如果不存在则返回None
    """
    post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if post:
        post.is_human_user_liked = 1 if is_liked else 0
        if is_liked:
            post.like_count += 1
        else:
            post.like_count = max(0, post.like_count - 1)
        db.commit()
        db.refresh(post)
    return post


def update_comment_like_status(db: Session, comment_id: int, is_liked: bool) -> Optional[models.Comment]:
    """
    更新评论的点赞状态
    
    Args:
        db: 数据库会话
        comment_id: 评论ID
        is_liked: 是否已点赞
        
    Returns:
        Optional[models.Comment]: 更新后的评论对象，如果不存在则返回None
    """
    comment = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()
    if comment:
        comment.is_human_user_liked = 1 if is_liked else 0
        if is_liked:
            comment.comment_likes += 1
        else:
            comment.comment_likes = max(0, comment.comment_likes - 1)
        db.commit()
        db.refresh(comment)
    return comment


def get_human_user_by_username(db: Session, username: str) -> Optional[models.HumanUser]:
    """
    根据用户名获取人类用户
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        Optional[models.HumanUser]: 人类用户对象，如果不存在则返回None
    """
    return db.query(models.HumanUser).filter(models.HumanUser.username == username).first()


def create_human_user(db: Session, username: str, user_template_id: int, avatar_path: str = "") -> models.HumanUser:
    """
    创建人类用户
    
    Args:
        db: 数据库会话
        username: 用户名
        user_template_id: 用户模板ID
        avatar_path: 头像路径
        
    Returns:
        models.HumanUser: 创建的人类用户对象
    """
    logger.debug(f"开始创建人类用户，用户名: {username}, 模板ID: {user_template_id}")
    
    # 获取用户模板以获取follower_count
    template = get_user_template_by_id(db, user_template_id)
    if not template:
        raise ValueError(f"未找到模板ID: {user_template_id}")
    
    # 创建人类用户
    db_human_user = models.HumanUser(
        username=username,
        user_template_id=user_template_id,
        avatar_path=avatar_path,
        follower_count=template.follower_count,  # 从模板获取follower_count
        created_at=datetime.now()  # 自动生成created_at
    )
    
    db.add(db_human_user)
    db.commit()
    db.refresh(db_human_user)
    
    logger.info(f"成功创建人类用户，ID: {db_human_user.user_id}，用户名: {db_human_user.username}")
    return db_human_user


def delete_human_user(db: Session, human_user_id: int) -> dict:
    """
    删除人类用户及其所有关联数据
    
    Args:
        db: 数据库会话
        human_user_id: 人类用户ID
        
    Returns:
        dict: 包含删除统计信息的字典
        
    Raises:
        ValueError: 如果用户不存在
    """
    logger.debug(f"开始删除人类用户，ID: {human_user_id}")
    
    # 验证用户是否存在
    human_user = get_human_user_by_id(db, human_user_id)
    if not human_user:
        raise ValueError(f"未找到用户ID为 {human_user_id} 的用户")
    
    username = human_user.username
    
    # 统计变量
    deleted_posts_count = 0
    deleted_ai_users_count = 0
    deleted_comments_count = 0
    deleted_human_comments_count = 0
    deleted_ai_comments_count = 0
    
    try:
        # 1. 删除该用户所有AI用户发布的评论
        ai_users = get_ai_users_by_human_user_id(db, human_user_id)
        for ai_user in ai_users:
            ai_comments = db.query(models.Comment).filter(
                models.Comment.sender_id == ai_user.user_id,
                models.Comment.sender_type == "ai_user"
            ).all()
            deleted_ai_comments_count += len(ai_comments)
            for comment in ai_comments:
                db.delete(comment)
        
        # 2. 删除该用户自己发布的评论
        human_comments = db.query(models.Comment).filter(
            models.Comment.sender_id == str(human_user_id),
            models.Comment.sender_type == "human_user"
        ).all()
        deleted_human_comments_count += len(human_comments)
        for comment in human_comments:
            db.delete(comment)
        
        deleted_comments_count = deleted_ai_comments_count + deleted_human_comments_count
        
        # 3. 删除该用户发布的所有帖子（级联删除帖子的评论）
        posts = db.query(models.Post).filter(models.Post.author_id == human_user_id).all()
        deleted_posts_count = len(posts)
        for post in posts:
            # 删除帖子的所有评论（包括其他用户的评论）
            post_comments = db.query(models.Comment).filter(models.Comment.post_id == post.post_id).all()
            for comment in post_comments:
                db.delete(comment)
            # 删除帖子
            db.delete(post)
        
        # 4. 删除该用户的所有AI用户
        deleted_ai_users_count = len(ai_users)
        for ai_user in ai_users:
            db.delete(ai_user)
        
        # 5. 删除人类用户本身
        db.delete(human_user)
        
        # 提交事务
        db.commit()
        
        logger.info(f"成功删除人类用户: {username} (ID: {human_user_id})")
        logger.info(f"删除统计 - 帖子: {deleted_posts_count}, AI用户: {deleted_ai_users_count}, 评论: {deleted_comments_count}")
        
        return {
            "deleted_user_id": human_user_id,
            "deleted_username": username,
            "deleted_posts_count": deleted_posts_count,
            "deleted_ai_users_count": deleted_ai_users_count,
            "deleted_comments_count": deleted_comments_count,
            "deleted_human_comments_count": deleted_human_comments_count,
            "deleted_ai_comments_count": deleted_ai_comments_count
        }
        
    except Exception as e:
        # 回滚事务
        db.rollback()
        logger.error(f"删除人类用户失败: {e}")
        raise


def get_posts_likes_batch(db: Session, post_ids: List[int]) -> dict:
    """
    批量获取帖子点赞信息
    
    Args:
        db: 数据库会话
        post_ids: 帖子ID列表
        
    Returns:
        dict: 格式为 {post_id: {"likes": int, "isLiked": bool}}
    """
    if not post_ids:
        return {}
    
    posts = db.query(models.Post).filter(models.Post.post_id.in_(post_ids)).all()
    
    result = {}
    for post in posts:
        result[post.post_id] = {
            "likes": post.like_count,
            "isLiked": post.is_human_user_liked == 1
        }
    
    logger.debug(f"批量获取 {len(post_ids)} 个帖子的点赞信息，实际返回 {len(result)} 个")
    return result


def get_comments_likes_batch(db: Session, comment_ids: List[int]) -> dict:
    """
    批量获取评论点赞信息
    
    Args:
        db: 数据库会话
        comment_ids: 评论ID列表
        
    Returns:
        dict: 格式为 {comment_id: {"likes": int, "isLiked": bool}}
    """
    if not comment_ids:
        return {}
    
    comments = db.query(models.Comment).filter(models.Comment.comment_id.in_(comment_ids)).all()
    
    result = {}
    for comment in comments:
        result[comment.comment_id] = {
            "likes": comment.comment_likes,
            "isLiked": comment.is_human_user_liked == 1
        }
    
    logger.debug(f"批量获取 {len(comment_ids)} 个评论的点赞信息，实际返回 {len(result)} 个")
    return result

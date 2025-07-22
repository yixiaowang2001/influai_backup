import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    post_content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    comments = relationship("Comment", back_populates="post")

    def __repr__(self):
        content_preview = self.post_content[:50] + "..." if len(self.post_content) > 50 else self.post_content
        return f"<Post(id={self.post_id}, content='{content_preview}', likes={self.like_count})>"

    def __str__(self):
        return f"帖子#{self.post_id}: {self.post_content[:30]}... (点赞:{self.like_count})"


class AIUser(Base):
    __tablename__ = "ai_users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), nullable=False)
    avatar_path = Column(String(255), default="")
    attitude_value = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)

    comments = relationship("Comment", back_populates="ai_user")

    def __repr__(self):
        return f"<AIUser(id='{self.user_id}', username='{self.username}', attitude={self.attitude_value})>"

    def __str__(self):
        return f"AI用户: {self.username} (态度值: {self.attitude_value})"


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    comment_content = Column(Text, nullable=False)
    comment_user_type = Column(Integer, nullable=False)
    comment_level = Column(Integer, nullable=False)
    comment_likes = Column(Integer, default=0)
    master_comment_id = Column(Integer, ForeignKey("comments.comment_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    send_at = Column(DateTime, nullable=True)

    post_id = Column(Integer, ForeignKey("posts.post_id"), nullable=False)
    ai_user_id = Column(String(36), ForeignKey("ai_users.user_id"), nullable=True)

    post = relationship("Post", back_populates="comments")
    ai_user = relationship("AIUser", back_populates="comments")

    parent_comment = relationship("Comment", remote_side=[comment_id])

    def __repr__(self):
        content_preview = self.comment_content[:30] + "..." if len(self.comment_content) > 30 else self.comment_content
        return f"<Comment(id={self.comment_id}, content='{content_preview}', likes={self.comment_likes})>"

    def __str__(self):
        return f"评论#{self.comment_id}: {self.comment_content[:20]}... (点赞:{self.comment_likes})"


class UserTemplate(Base):
    __tablename__ = "user_templates"

    template_id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)
    persona = Column(Text, nullable=False)
    follower_count = Column(Integer, default=0)
    commenter_distribution = Column(JSON, nullable=False)
    default_avatar_path = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<UserTemplate(id={self.template_id}, name='{self.template_name}', followers={self.follower_count})>"

    def __str__(self):
        return f"用户模板: {self.template_name} (粉丝数: {self.follower_count})"

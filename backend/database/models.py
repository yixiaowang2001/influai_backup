from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    post_content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    comments = relationship("Comment", back_populates="post")


class AIUser(Base):
    __tablename__ = "ai_users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    avatar_path = Column(String(255), default="")
    attitude_value = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)

    comments = relationship("Comment", back_populates="ai_user")


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
    ai_user_id = Column(Integer, ForeignKey("ai_users.user_id"), nullable=True)

    post = relationship("Post", back_populates="comments")
    ai_user = relationship("AIUser", back_populates="comments")

    parent_comment = relationship("Comment", remote_side=[comment_id])
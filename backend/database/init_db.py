from backend.database.database import engine, Base, get_db_session
from backend.database import models
from backend.models import AIUser as AIUserModel, Post as PostModel, Comment as CommentModel, Attitude
from datetime import datetime
import os
from backend.utils import get_logger

logger = get_logger(__name__)


def create_tables():
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功！")


def insert_sample_data():
    """插入示例数据"""
    print("正在插入示例数据...")

    db = get_db_session()
    try:
        # 检查是否已经有数据
        if db.query(models.Post).first():
            print("⚠️  数据已存在，跳过示例数据插入")
            return

        # 1. 创建示例帖子
        sample_posts = [
            models.Post(
                post_content="欢迎来到我们的社区！这里是第一个帖子。",
                like_count=5
            ),
            models.Post(
                post_content="今天天气真不错，大家都在做什么呢？",
                like_count=3
            )
        ]

        for post in sample_posts:
            db.add(post)
        db.commit()

        # 2. 创建示例AI用户
        sample_ai_users = [
            models.AIUser(
                username="智能助手小王",
                avatar_path="/avatars/ai_001.png",
                attitude_value=0.8
            ),
            models.AIUser(
                username="AI评论员",
                avatar_path="/avatars/ai_002.png",
                attitude_value=0.6
            )
        ]

        for ai_user in sample_ai_users:
            db.add(ai_user)
        db.commit()

        # 3. 创建示例评论
        posts = db.query(models.Post).all()
        ai_users = db.query(models.AIUser).all()

        sample_comments = [
            models.Comment(
                comment_content="很棒的社区，期待更多精彩内容！",
                comment_user_type=1,
                comment_level=1,
                comment_likes=2,
                post_id=posts[0].post_id,
                ai_user_id=ai_users[0].user_id
            ),
            models.Comment(
                comment_content="天气确实不错，我在学习新技术",
                comment_user_type=1,
                comment_level=1,
                comment_likes=1,
                post_id=posts[1].post_id,
                ai_user_id=ai_users[1].user_id
            )
        ]

        for comment in sample_comments:
            db.add(comment)
        db.commit()

        print("✅ 示例数据插入成功！")

    except Exception as e:
        print(f"❌ 插入示例数据时出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database(with_sample_data: bool = True):
    """完整初始化数据库"""
    print("🚀 开始初始化数据库...")

    try:
        # 1. 创建表
        create_tables()

        # 2. 插入示例数据（可选）
        if with_sample_data:
            insert_sample_data()

        print("✅ 数据库初始化完成！")
        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    init_database(with_sample_data=True)
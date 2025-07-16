from backend.database import models
from backend.database.database import engine, Base, get_db_session
from backend.utils import get_logger

logger = get_logger(__name__)


def create_tables() -> None:
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
    logger.info('数据库表已创建')


def insert_init_data() -> None:
    """插入初始数据"""
    db = get_db_session()
    try:
        if db.query(models.Post).first():
            logger.info("数据库已初始化。")
            return

        # 初始化AI用户数据
        init_ai_users = [
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

        for ai_user in init_ai_users:
            db.add(ai_user)
        db.commit()

        logger.info("成功插入初始数据。")

    except Exception as e:
        logger.error(f"插入初始数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database() -> bool:
    """
    初始化数据库
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        create_tables()
        insert_init_data()
        logger.info("数据库初始化完成")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

from backend.database import models
from backend.database.database import engine, Base, get_db_session
from backend.utils import get_logger
from backend.database.db_utils import init_ai_users

logger = get_logger(__name__)


def create_tables() -> None:
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
    logger.info('数据库表已创建')


def insert_init_data(user_template: dict) -> None:
    """插入初始数据"""
    db = get_db_session()
    try:
        if db.query(models.Post).first():
            logger.info("数据库已初始化。")
            return

        # 初始化AI用户数据
        init_ai_users = init_ai_users(100)

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


def init_database(user_template: dict) -> bool:
    """
    初始化数据库
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        create_tables()
        insert_init_data(user_template)
        logger.info("数据库初始化完成")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

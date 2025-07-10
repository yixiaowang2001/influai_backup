from backend.database import models
from backend.database.database import engine, Base, get_db_session
from backend.utils import get_logger

logger = get_logger(__name__)


def create_tables():
    Base.metadata.create_all(bind=engine)
    logger.info('Tables created')


def insert_init_data():
    db = get_db_session()
    try:
        if db.query(models.Post).first():
            logger.info("Database already initialized.")
            return

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

        logger.info("Successfully inserted init data.")

    except Exception as e:
        logger.error(f"Failed to insert init data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    try:
        create_tables()
        insert_init_data()
        logger.info("Database initialized")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize the database: {e}")
        return False

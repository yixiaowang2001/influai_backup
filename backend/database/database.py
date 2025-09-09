from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from configs.database_config import DatabaseConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# 延迟初始化数据库引擎
_engine = None
_SessionLocal = None


def get_engine():
    """获取数据库引擎，延迟初始化"""
    global _engine
    if _engine is None:
        DATABASE_URL = DatabaseConfig.get_database_url()
        ENGINE_KWARGS = DatabaseConfig.get_engine_kwargs()

        logger.info(f"数据库类型: {DatabaseConfig.get_db_type()}")
        logger.info(f"数据库URL: {DATABASE_URL}")

        _engine = create_engine(DATABASE_URL, **ENGINE_KWARGS)
    return _engine


def get_session_local():
    """获取会话工厂，延迟初始化"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# 创建基础类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话生成器
    
    Yields:
        Session: 数据库会话
    """
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    获取数据库会话
    
    Returns:
        Session: 数据库会话
    """
    return get_session_local()()


# 为了向后兼容，提供engine属性
def engine():
    return get_engine()

import json
import os
from typing import Dict, Any

from backend.database import models
from backend.database.database import engine, Base, get_db_session
from backend.database.db_utils import init_ai_users
from backend.utils import get_logger

logger = get_logger(__name__)


def load_user_templates() -> Dict[str, Any]:
    """
    从JSON文件加载用户模板数据
    
    Returns:
        Dict[str, Any]: 用户模板数据字典
    """
    try:
        # 获取JSON文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "..", "data", "user_templates.json")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        logger.info(f"成功加载用户模板数据，共 {len(templates)} 个模板")
        return templates
    
    except FileNotFoundError:
        logger.error(f"用户模板JSON文件未找到: {json_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件格式错误: {e}")
        raise
    except Exception as e:
        logger.error(f"加载用户模板数据失败: {e}")
        raise


def init_user_templates() -> bool:
    """
    初始化用户模板数据到数据库
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        db = get_db_session()
        
        # 检查是否已经初始化
        if db.query(models.UserTemplate).first():
            logger.info("用户模板数据已存在，跳过初始化")
            return True
        
        # 加载模板数据
        templates_data = load_user_templates()
        
        # 创建模板对象并插入数据库
        for template_name, template_data in templates_data.items():
            user_template = models.UserTemplate(
                template_name=template_name,
                persona=template_data["persona"],
                follower_count=template_data["follower_count"],
                commenter_distribution=template_data["commenter_distribution"],
                default_avatar_path=template_data.get("default_avatar_path", "")
            )
            db.add(user_template)
        
        db.commit()
        logger.info(f"成功初始化 {len(templates_data)} 个用户模板")
        return True
        
    except Exception as e:
        logger.error(f"初始化用户模板失败: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()


def get_user_template_by_name(template_name: str) -> models.UserTemplate:
    """
    根据模板名称获取用户模板
    
    Args:
        template_name (str): 模板名称
        
    Returns:
        models.UserTemplate: 用户模板对象
    """
    db = get_db_session()
    try:
        template = db.query(models.UserTemplate).filter(
            models.UserTemplate.template_name == template_name
        ).first()
        return template
    finally:
        db.close()


def get_all_user_templates() -> list[models.UserTemplate]:
    """
    获取所有用户模板
    
    Returns:
        list[models.UserTemplate]: 所有用户模板列表
    """
    db = get_db_session()
    try:
        templates = db.query(models.UserTemplate).all()
        return templates
    finally:
        db.close()


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

        # 初始化用户模板数据
        if not init_user_templates():
            raise Exception("用户模板初始化失败")

        # 如果提供了用户模板，则初始化AI用户数据
        if user_template and 'follower_count' in user_template:
            all_ai_users = init_ai_users(user_template)
            for ai_user in all_ai_users:
                db.add(ai_user)
            db.commit()
            logger.info("成功插入AI用户数据。")
        else:
            logger.info("跳过AI用户数据初始化（未提供用户模板）")

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

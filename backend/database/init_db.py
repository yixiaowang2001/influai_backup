import json
import os
from typing import Dict, Any

# 直接设置环境变量，确保MySQL连接正常
os.environ["DB_TYPE"] = "mysql"
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_PORT"] = "3306"
os.environ["MYSQL_USER"] = "root"
os.environ["MYSQL_PASSWORD"] = "influai"
os.environ["MYSQL_DATABASE"] = "influai"
os.environ["MYSQL_CHARSET"] = "utf8mb4"

from backend.database import models
from backend.database.crud import get_user_template_by_name
from backend.database.database import get_engine, Base, get_db_session
from backend.utils.db_utils import init_ai_users
from backend.utils.logger import get_logger

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

        # 如果文件不存在，尝试从项目根目录查找
        if not os.path.exists(json_path):
            project_root = os.path.join(current_dir, "..", "..")
            json_path = os.path.join(project_root, "backend", "data", "user_templates.json")

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


def create_tables() -> None:
    """创建数据库表"""
    Base.metadata.create_all(bind=get_engine())
    logger.info('数据库表已创建')


def insert_init_data(template_name: str = None) -> None:
    """插入初始数据"""
    db = get_db_session()
    try:
        if db.query(models.Post).first():
            logger.info("数据库已初始化。")
            return

        # 初始化用户模板数据
        if not init_user_templates():
            raise Exception("用户模板初始化失败")

        # 不再自动创建默认人类用户
        logger.info("跳过默认人类用户创建，用户将通过API接口手动创建")

        # 如果提供了模板名称，则根据该模板初始化AI用户数据
        if template_name:
            template = get_user_template_by_name(db, template_name)
            if template:
                # 将数据库对象转换为字典格式
                user_template_dict = {
                    "persona": template.persona,
                    "follower_count": template.follower_count,
                    "commenter_distribution": template.commenter_distribution,
                    "default_avatar_path": template.default_avatar_path
                }
                # 注意：此处没有 human_user_id，维持原逻辑行为
                all_ai_users = init_ai_users(user_template_dict, human_user_id=0)
                for ai_user in all_ai_users:
                    db.add(ai_user)
                db.commit()
                logger.info(f"成功根据模板 '{template_name}' 插入AI用户数据。")
            else:
                logger.warning(f"未找到模板: {template_name}")
        else:
            logger.info("跳过AI用户数据初始化（未提供模板名称）")

        logger.info("成功插入初始数据。")

    except Exception as e:
        logger.error(f"插入初始数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database(template_name: str = None) -> bool:
    """
    初始化数据库
    
    Args:
        template_name: 要用于初始化AI用户的模板名称，如果为None则只初始化用户模板
        
    Returns:
        bool: 初始化是否成功
    """
    try:
        create_tables()
        insert_init_data(template_name)
        logger.info("数据库初始化完成")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

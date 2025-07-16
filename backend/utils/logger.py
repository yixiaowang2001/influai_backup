import logging
from pathlib import Path

from backend.configs import IS_DEBUG

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR
LOG_FILE = LOG_DIR / 'backend_debug.log'

LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG if IS_DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)

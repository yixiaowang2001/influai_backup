import logging
from pathlib import Path
from datetime import datetime

from ..configs import IS_DEBUG

# 尝试导入增强日志系统
try:
    from .enhanced_logger import enhanced_logger, LogEvents
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False

# 只有在增强日志系统不可用时才配置传统日志
if not ENHANCED_LOGGING_AVAILABLE:
    PROJECT_DIR = Path(__file__).parent.parent
    LOG_DIR = PROJECT_DIR
    LOG_FILE = LOG_DIR / 'backend_debug.log'
    
    LOG_DIR.mkdir(exist_ok=True)
    
    # 避免重复配置
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.DEBUG if IS_DEBUG else logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
else:
    # 如果有增强日志系统，则禁用根日志记录器的处理器以避免冲突
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    # 设置一个不输出的处理器，避免日志丢失
    null_handler = logging.NullHandler()
    root_logger.addHandler(null_handler)

def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    if ENHANCED_LOGGING_AVAILABLE:
        # 根据名称映射到不同的增强日志记录器
        if 'main' in name or 'api' in name:
            return enhanced_logger.api_logger
        elif 'crud' in name or 'database' in name:
            return enhanced_logger.business_logger
        elif 'celery' in name or 'task' in name:
            return enhanced_logger.celery_logger
        else:
            return enhanced_logger.business_logger
    else:
        return logging.getLogger(name)

def log_business_event(event_type, details=None, user_id=None):
    """业务事件日志记录"""
    if ENHANCED_LOGGING_AVAILABLE:
        LogEvents.business_event(event_type, details, user_id)
    else:
        logger = logging.getLogger("business")
        message = f"{event_type.upper()}"
        if user_id:
            message += f" [User:{user_id}]"
        if details:
            message += f" - {details}"
        logger.info(message)

def log_api_event(method, path, status_code, duration_ms=None, user_id=None):
    """API事件日志记录"""
    if ENHANCED_LOGGING_AVAILABLE:
        LogEvents.api_event(method, path, status_code, duration_ms, user_id)
    else:
        logger = logging.getLogger("api")
        message = f"{method} {path} - {status_code}"
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"
        if user_id:
            message += f" [User:{user_id}]"
        logger.info(message)

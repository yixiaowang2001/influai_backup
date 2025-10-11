#!/usr/bin/env python3
"""
增强的日志管理器
统一管理所有日志输出，支持文件持久化和按天分片存储
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime, timedelta
import os
import glob

class EnhancedLogger:
    """增强的日志管理器"""
    
    def __init__(self, name="InfluAI"):
        self.name = name
        self.logs_dir = Path(__file__).parent.parent.parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self._loggers = {}
        
    def setup_loggers(self):
        """设置所有日志记录器"""
        
        # 清理旧的日志文件
        self._cleanup_old_logs()
        
        # 主应用日志 - 系统启动、关闭、进程管理
        self.app_logger = self._create_logger(
            "app", "app.log", 
            format_style="detailed",
            console_output=True
        )
        
        # 业务事件日志 - 用户操作、帖子、评论、AI事件
        self.business_logger = self._create_logger(
            "business", "business.log",
            format_style="business"
        )
        
        # API请求日志
        self.api_logger = self._create_logger(
            "api", "api.log",
            format_style="api"
        )
        
        # 错误日志 - 所有WARNING及以上级别
        self.error_logger = self._create_logger(
            "error", "error.log",
            format_style="detailed",
            level=logging.WARNING,
            console_output=True
        )
        
        # Celery任务日志
        self.celery_logger = self._create_logger(
            "celery", "celery_worker.log",
            format_style="detailed"
        )
        
        # 前端服务器日志
        self.frontend_logger = self._create_logger(
            "frontend", "frontend.log",
            format_style="simple"
        )
        
        return self
    
    def _create_logger(self, name, filename, format_style="simple", 
                      level=logging.INFO, console_output=False):
        """创建单个日志记录器"""
        
        full_name = f"{self.name}.{name}"
        
        # 如果已存在，直接返回
        if full_name in self._loggers:
            return self._loggers[full_name]
            
        logger = logging.getLogger(full_name)
        logger.setLevel(level)
        
        # 清除可能存在的处理器
        logger.handlers.clear()
        
        # 文件处理器（按天存储）
        # 直接使用带日期的文件名，简单而直接
        today = datetime.now().strftime('%Y-%m-%d')
        base_name = filename.replace('.log', '')
        daily_filename = f"{base_name}_{today}.log"
        daily_file_path = self.logs_dir / daily_filename
        
        file_handler = logging.FileHandler(
            daily_file_path,
            mode='a',  # 追加模式
            encoding='utf-8'
        )
        
        # 设置格式
        formatter = self._get_formatter(format_style)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 可选的控制台输出
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 防止重复日志
        logger.propagate = False
        
        self._loggers[full_name] = logger
        return logger
    
    def _get_formatter(self, style):
        """获取日志格式器 - 无emoji符号"""
        formats = {
            "simple": "%(asctime)s [%(levelname)s] %(message)s",
            "detailed": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s - (%(filename)s:%(lineno)d)",
            "business": "%(asctime)s [BUSINESS] %(message)s",
            "api": "%(asctime)s [API] %(message)s"
        }
        
        return logging.Formatter(
            formats.get(style, formats["simple"]),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _cleanup_old_logs(self, keep_days=30):
        """清理超过指定天数的旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            # 查找所有带日期的日志文件
            log_pattern = str(self.logs_dir / "*_????-??-??.log")
            old_files = []
            
            for log_file in glob.glob(log_pattern):
                file_path = Path(log_file)
                filename = file_path.name
                
                # 提取日期部分 (格式: name_YYYY-MM-DD.log)
                parts = filename.split('_')
                if len(parts) >= 2:
                    date_part = parts[-1].replace('.log', '')
                    if len(date_part) == 10 and date_part.count('-') == 2:  # YYYY-MM-DD
                        if date_part < cutoff_str:
                            old_files.append(file_path)
            
            # 删除旧文件
            deleted_count = 0
            for old_file in old_files:
                try:
                    old_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"删除日志文件失败 {old_file.name}: {e}")
            
            if deleted_count > 0:
                print(f"已清理 {deleted_count} 个旧日志文件 (超过{keep_days}天)")
                    
        except Exception as e:
            print(f"清理旧日志文件时出错: {e}")
    
    def get_logger(self, name):
        """获取指定的日志记录器"""
        full_name = f"{self.name}.{name}"
        return self._loggers.get(full_name)

# 便捷的日志记录函数
class LogEvents:
    """统一的日志事件记录"""
    
    @staticmethod
    def system_event(event, details=None):
        """系统事件记录"""
        message = f"SYSTEM: {event}"
        if details:
            message += f" - {details}"
        enhanced_logger.app_logger.info(message)
    
    @staticmethod
    def service_status(service_name, status, details=None):
        """服务状态记录"""
        message = f"SERVICE: {service_name} - {status.upper()}"
        if details:
            message += f" - {details}"
        
        if status.lower() in ["success", "started", "running"]:
            enhanced_logger.app_logger.info(message)
        elif status.lower() in ["failed", "error", "stopped"]:
            enhanced_logger.error_logger.error(message)
        else:
            enhanced_logger.app_logger.info(message)
    
    @staticmethod
    def business_event(event_type, details=None, user_id=None):
        """业务事件记录"""
        message = f"{event_type.upper()}"
        if user_id:
            message += f" [User:{user_id}]"
        if details:
            message += f" - {details}"
        enhanced_logger.business_logger.info(message)
    
    @staticmethod
    def api_event(method, path, status_code, duration_ms=None, user_id=None):
        """API请求事件记录"""
        message = f"{method} {path} - {status_code}"
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"
        if user_id:
            message += f" [User:{user_id}]"
        enhanced_logger.api_logger.info(message)
    
    @staticmethod
    def error_event(error_type, error_msg, context=None):
        """错误事件记录"""
        message = f"ERROR: {error_type} - {error_msg}"
        if context:
            message += f" - Context: {context}"
        enhanced_logger.error_logger.error(message)
    
    @staticmethod
    def celery_event(task_name, status, details=None):
        """Celery任务事件记录"""
        message = f"TASK: {task_name} - {status.upper()}"
        if details:
            message += f" - {details}"
        enhanced_logger.celery_logger.info(message)

# 全局日志管理器实例
enhanced_logger = EnhancedLogger()
enhanced_logger.setup_loggers()

def get_enhanced_logger(name=None):
    """获取增强日志记录器的便捷函数"""
    if name:
        return enhanced_logger.get_logger(name)
    return enhanced_logger.app_logger
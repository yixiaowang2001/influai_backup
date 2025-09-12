import os
from pathlib import Path

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    # 加载项目根目录的.env文件
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
    else:
        print(f"环境变量文件不存在: {env_path}")
except ImportError:
    print("python-dotenv未安装，跳过.env文件加载")

class DatabaseConfig:
    """数据库配置类"""
    
    # SQLite配置（作为备用）
    PROJECT_ROOT = Path(__file__).parent.parent
    DATABASE_DIR = PROJECT_ROOT / "database"
    DATABASE_PATH = PROJECT_ROOT / "database" / "app.db"
    
    @classmethod
    def get_db_type(cls) -> str:
        """获取数据库类型"""
        return os.getenv("DB_TYPE", "mysql")
    
    @classmethod
    def get_mysql_host(cls) -> str:
        """获取MySQL主机"""
        return os.getenv("MYSQL_HOST", "localhost")
    
    @classmethod
    def get_mysql_port(cls) -> int:
        """获取MySQL端口"""
        return int(os.getenv("MYSQL_PORT", "3306"))
    
    @classmethod
    def get_mysql_user(cls) -> str:
        """获取MySQL用户名"""
        return os.getenv("MYSQL_USER", "root")
    
    @classmethod
    def get_mysql_password(cls) -> str:
        """获取MySQL密码"""
        return os.getenv("MYSQL_PASSWORD", "influai")
    
    @classmethod
    def get_mysql_database(cls) -> str:
        """获取MySQL数据库名"""
        return os.getenv("MYSQL_DATABASE", "influai")
    
    @classmethod
    def get_mysql_charset(cls) -> str:
        """获取MySQL字符集"""
        return os.getenv("MYSQL_CHARSET", "utf8mb4")
    
    @classmethod
    def print_config(cls):
        """打印当前配置信息"""
        print("=== 数据库配置信息 ===")
        print(f"DB_TYPE: {cls.get_db_type()}")
        print(f"MYSQL_HOST: {cls.get_mysql_host()}")
        print(f"MYSQL_PORT: {cls.get_mysql_port()}")
        print(f"MYSQL_USER: {cls.get_mysql_user()}")
        print(f"MYSQL_PASSWORD: {'*' * len(cls.get_mysql_password()) if cls.get_mysql_password() else 'None'}")
        print(f"MYSQL_DATABASE: {cls.get_mysql_database()}")
        print(f"MYSQL_CHARSET: {cls.get_mysql_charset()}")
        print(f"DATABASE_PATH: {cls.DATABASE_PATH}")
        print("=====================")
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        if cls.get_db_type().lower() == "mysql":
            url = (
                f"mysql+pymysql://{cls.get_mysql_user()}:{cls.get_mysql_password()}"
                f"@{cls.get_mysql_host()}:{cls.get_mysql_port()}/{cls.get_mysql_database()}"
                f"?charset={cls.get_mysql_charset()}"
            )
            print(f"生成的MySQL URL: {url}")
            return url
        else:
            # 默认使用SQLite
            cls.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{cls.DATABASE_PATH}"
            print(f"生成的SQLite URL: {url}")
            return url
    
    @classmethod
    def get_engine_kwargs(cls) -> dict:
        """获取数据库引擎参数"""
        if cls.get_db_type().lower() == "mysql":
            return {
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "echo": False
            }
        else:
            return {
                "connect_args": {"check_same_thread": False},
                "echo": False
            }

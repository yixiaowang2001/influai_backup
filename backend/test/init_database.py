#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

用于初始化数据库和加载用户模板数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ["DB_TYPE"] = "mysql"
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_PORT"] = "3306"
os.environ["MYSQL_USER"] = "root"
os.environ["MYSQL_PASSWORD"] = "influai"
os.environ["MYSQL_DATABASE"] = "influai"
os.environ["MYSQL_CHARSET"] = "utf8mb4"

from backend.database.init_db import init_database

def main():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    try:
        # 初始化数据库（不指定模板名称，只初始化用户模板）
        success = init_database()
        
        if success:
            print("数据库初始化成功！")
            print("用户模板数据已加载到数据库中")
        else:
            print("数据库初始化失败！")
            
    except Exception as e:
        print(f"初始化过程中发生错误: {e}")

if __name__ == "__main__":
    main()

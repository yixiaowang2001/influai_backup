#!/usr/bin/env python3
"""
快速清理数据库数据的简化脚本
一键清空所有数据，无需交互确认
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["DB_TYPE"] = "mysql"
os.environ["MYSQL_HOST"] = "localhost"
os.environ["MYSQL_PORT"] = "3306"
os.environ["MYSQL_USER"] = "root"
os.environ["MYSQL_PASSWORD"] = "influai"
os.environ["MYSQL_DATABASE"] = "influai"
os.environ["MYSQL_CHARSET"] = "utf8mb4"

from backend.database.database import get_db_session
from backend.database import models

def quick_clear():
    """快速清空所有数据"""
    
    print("🚀 快速清理数据库数据...")
    
    db = None
    try:
        db = get_db_session()
        
        # 统计当前数据量
        comments_count = db.query(models.Comment).count()
        ai_users_count = db.query(models.AIUser).count()
        human_users_count = db.query(models.HumanUser).count()
        posts_count = db.query(models.Post).count()
        templates_count = db.query(models.UserTemplate).count()
        
        total_records = comments_count + ai_users_count + human_users_count + posts_count + templates_count
        
        if total_records == 0:
            print("✅ 数据库已经是空的")
            return
        
        print(f"发现 {total_records} 条记录，开始清理...")
        
        # 按依赖关系顺序删除
        deleted = 0
        
        # 删除评论
        if comments_count > 0:
            count = db.query(models.Comment).delete()
            deleted += count
            print(f"  - 删除了 {count} 条评论")
        
        # 删除AI用户
        if ai_users_count > 0:
            count = db.query(models.AIUser).delete()
            deleted += count
            print(f"  - 删除了 {count} 个AI用户")
        
        # 删除帖子
        if posts_count > 0:
            count = db.query(models.Post).delete()
            deleted += count
            print(f"  - 删除了 {count} 条帖子")
        
        # 删除人类用户
        if human_users_count > 0:
            count = db.query(models.HumanUser).delete()
            deleted += count
            print(f"  - 删除了 {count} 个人类用户")
        
        # 删除用户模板
        if templates_count > 0:
            count = db.query(models.UserTemplate).delete()
            deleted += count
            print(f"  - 删除了 {count} 个用户模板")
        
        # 提交事务
        db.commit()
        
        print(f"🎉 清理完成！共删除 {deleted} 条记录")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    quick_clear()

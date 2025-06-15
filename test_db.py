import sqlite3
import os
import unittest

# 数据库路径（当前目录下）
DB_PATH = "test_db.sqlite"


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库和表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            """)
            # 更多表结构...

    def get_connection(self):
        """获取数据库连接（用于事务控制）"""
        return sqlite3.connect(self.db_path)

    def create_user(self, name, email):
        """插入用户数据（参数化查询）"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    (name, email)
                )
                return cursor.lastrowid  # 返回新插入的ID
            except sqlite3.IntegrityError as e:
                print(f"唯一约束冲突: {e}")
                raise

    def delete_user(self, user_id):
        """按ID删除用户"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def get_user_by_id(self, user_id):
        """按ID查询用户"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, name, email FROM users WHERE id = ?",
                (user_id,)
            )
            return cursor.fetchone()  # 返回单条记录

    def clear_test_data(self):
        """清理所有测试数据（测试用）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM users")
            conn.execute("UPDATE SQLITE_SEQUENCE SET seq = 0 WHERE name = 'users'")  # 重置自增ID


# 单元测试（含数据清理）
class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseManager(DB_PATH)

    def tearDown(self):
        # 每个测试结束后清理数据
        self.db.clear_test_data()

    def test_user_lifecycle(self):
        # 测试创建用户
        user_id = self.db.create_user("Alice", "alice@example.com")
        self.assertIsInstance(user_id, int)

        # 测试查询
        user = self.db.get_user_by_id(user_id)
        self.assertEqual(user[1], "Alice")

        # 测试删除
        self.db.delete_user(user_id)
        self.assertIsNone(self.db.get_user_by_id(user_id))

    def test_email_unique(self):
        self.db.create_user("Bob", "bob@example.com")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_user("Bob2", "bob@example.com")  # 重复邮箱应失败


if __name__ == "__main__":
    # 执行测试（测试后自动清理数据）
    unittest.main()

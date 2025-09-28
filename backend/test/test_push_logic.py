"""
推送逻辑测试脚本
"""
import asyncio
import json
from datetime import datetime
from backend.services.push_config import PushConfig, PushType, PushItem, PushConfigManager
from backend.services.push_examples import PushServiceManager


class MockConnectionManager:
    """模拟连接管理器，用于测试"""
    
    def __init__(self):
        self.messages = []
    
    async def broadcast(self, message: str):
        """模拟广播消息"""
        self.messages.append({
            "timestamp": datetime.now(),
            "message": json.loads(message)
        })
        print(f"[广播] {message}")


class MockDatabaseSession:
    """模拟数据库会话"""
    
    def __init__(self):
        self.comments = []
        self.committed = False
    
    def query(self, model):
        return MockQuery(model, self.comments)
    
    def commit(self):
        self.committed = True
    
    def close(self):
        pass


class MockQuery:
    """模拟查询对象"""
    
    def __init__(self, model, data):
        self.model = model
        self.data = data
    
    def filter(self, condition):
        return self
    
    def first(self):
        return None


class MockComment:
    """模拟评论对象"""
    
    def __init__(self, comment_id, content, sender_type="ai_user", sender_id="1"):
        self.comment_id = comment_id
        self.comment_content = content
        self.sender_type = sender_type
        self.sender_id = sender_id
        self.created_at = datetime.now()
        self.comment_likes = 0
        self.is_human_user_liked = 0
        self.send_at = None


class MockAIUser:
    """模拟AI用户"""
    
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username


class MockHumanUser:
    """模拟人类用户"""
    
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username


def mock_get_db_session():
    """模拟获取数据库会话"""
    return MockDatabaseSession()


def mock_crud_get_comments_by_post(db, post_id):
    """模拟获取评论"""
    # 创建一些测试评论
    comments = [
        MockComment(1, "这是一条测试评论1"),
        MockComment(2, "这是一条测试评论2"),
        MockComment(3, "这是一条测试评论3"),
        MockComment(4, "这是一条测试评论4"),
        MockComment(5, "这是一条测试评论5"),
    ]
    return comments


def mock_crud_get_ai_user(db, user_id):
    """模拟获取AI用户"""
    return MockAIUser(user_id, f"ai_user_{user_id}")


def mock_crud_get_human_user_by_id(db, user_id):
    """模拟获取人类用户"""
    return MockHumanUser(user_id, f"human_user_{user_id}")


async def test_push_logic():
    """测试推送逻辑"""
    print("开始测试通用推送逻辑...")
    
    # 创建模拟连接管理器
    mock_manager = MockConnectionManager()
    
    # 创建推送服务管理器
    push_service_manager = PushServiceManager(mock_manager)
    
    # 模拟数据库操作
    import backend.database.crud as crud
    crud.get_comments_by_post = mock_crud_get_comments_by_post
    crud.get_ai_user = mock_crud_get_ai_user
    crud.get_human_user_by_id = mock_crud_get_human_user_by_id
    
    # 测试配置1: 快速推送
    print("\n=== 测试快速推送配置 ===")
    fast_config = PushConfig(
        push_type=PushType.COMMENT,
        total_duration=30,  # 30秒
        base_interval=5.0,  # 5秒间隔
        random_variance=0.2,  # 20%波动
        batch_size=2,  # 每次2条
        initial_delay=1.0
    )
    
    task_id1 = await push_service_manager.start_comment_push(post_id=123, config=fast_config)
    print(f"启动快速推送任务: {task_id1}")
    
    # 等待任务完成
    await asyncio.sleep(35)
    
    # 检查推送结果
    print(f"\n快速推送完成，共推送 {len(mock_manager.messages)} 条消息")
    for i, msg in enumerate(mock_manager.messages):
        print(f"消息 {i+1}: {msg['message']['type']} - {msg['timestamp'].strftime('%H:%M:%S')}")
    
    # 清空消息
    mock_manager.messages.clear()
    
    # 测试配置2: 慢速推送
    print("\n=== 测试慢速推送配置 ===")
    slow_config = PushConfig(
        push_type=PushType.COMMENT,
        total_duration=20,  # 20秒
        base_interval=8.0,  # 8秒间隔
        random_variance=0.3,  # 30%波动
        batch_size=1,  # 每次1条
        initial_delay=0.5
    )
    
    task_id2 = await push_service_manager.start_comment_push(post_id=456, config=slow_config)
    print(f"启动慢速推送任务: {task_id2}")
    
    # 等待任务完成
    await asyncio.sleep(25)
    
    # 检查推送结果
    print(f"\n慢速推送完成，共推送 {len(mock_manager.messages)} 条消息")
    for i, msg in enumerate(mock_manager.messages):
        print(f"消息 {i+1}: {msg['message']['type']} - {msg['timestamp'].strftime('%H:%M:%S')}")
    
    # 测试任务管理
    print("\n=== 测试任务管理 ===")
    active_tasks = push_service_manager.get_active_tasks()
    print(f"当前活跃任务: {active_tasks}")
    
    print("\n推送逻辑测试完成！")


async def test_config_manager():
    """测试配置管理器"""
    print("\n=== 测试配置管理器 ===")
    
    # 测试默认配置
    comment_config = PushConfigManager.DEFAULT_COMMENT_CONFIG
    print(f"默认评论配置: {comment_config}")
    
    # 测试自定义配置
    custom_config = PushConfigManager.get_comment_config(
        total_duration=600,
        base_interval=15.0,
        batch_size=3
    )
    print(f"自定义评论配置: {custom_config}")
    
    # 测试点赞配置
    like_config = PushConfigManager.get_like_config(
        total_duration=180,
        base_interval=6.0,
        batch_size=2
    )
    print(f"点赞配置: {like_config}")


def test_push_item():
    """测试推送项目"""
    print("\n=== 测试推送项目 ===")
    
    # 创建推送项目
    push_item = PushItem(
        id="test_1",
        content={
            "id": "comment_1",
            "content": "测试评论内容",
            "author": {"id": "1", "username": "test_user"},
            "timestamp": "刚刚"
        },
        metadata={"comment_id": 1, "sender_type": "ai_user"}
    )
    
    print(f"推送项目: {push_item}")
    print(f"项目ID: {push_item.id}")
    print(f"内容: {push_item.content}")
    print(f"元数据: {push_item.metadata}")


if __name__ == "__main__":
    print("通用推送逻辑测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_push_logic())
    asyncio.run(test_config_manager())
    test_push_item()
    
    print("\n所有测试完成！")

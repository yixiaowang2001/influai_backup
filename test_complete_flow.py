#!/usr/bin/env python3
"""
测试完整流程：设置用户 -> 发布帖子 -> 自动生成评论
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_get_user_templates():
    """测试获取用户模板"""
    print("1. 获取用户模板列表...")
    try:
        response = requests.get(f"{BASE_URL}/user-templates")
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            print(f"✓ 成功获取 {len(templates)} 个模板")
            for template in templates:
                print(f"  - {template['name']}: ID={template['id']}")
            return templates
        else:
            print(f"✗ 获取模板失败: {response.text}")
            return []
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return []

def test_init_ai_users(template_name):
    """测试初始化AI用户"""
    print(f"\n2. 初始化AI用户（模板: {template_name}）...")
    try:
        response = requests.post(f"{BASE_URL}/user-templates/{template_name}/init-ai-users")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {data.get('message')}")
            return True
        else:
            print(f"✗ 初始化失败: {response.text}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_set_current_user(user_template_id):
    """测试设置当前用户"""
    print(f"\n3. 设置当前用户（模板ID: {user_template_id}）...")
    try:
        data = {"user_template_id": user_template_id}
        response = requests.post(f"{BASE_URL}/user/set-current", json=data)
        if response.status_code == 200:
            result = response.json()
            user_data = result.get("data", {})
            print(f"✓ 成功设置当前用户: {user_data.get('humanUsername')}")
            print(f"  用户ID: {user_data.get('humanUserId')}")
            return user_data.get("humanUserId")
        else:
            print(f"✗ 设置用户失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None

def test_get_current_user():
    """测试获取当前用户"""
    print("\n4. 获取当前用户信息...")
    try:
        response = requests.get(f"{BASE_URL}/user/current")
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})
            print(f"✓ 当前用户: {user_data.get('humanUsername')}")
            return user_data
        else:
            print(f"✗ 获取当前用户失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None

def test_create_post():
    """测试发布帖子"""
    print("\n5. 发布帖子...")
    try:
        data = {"content": "这是一条测试帖子，将会自动生成评论"}
        response = requests.post(f"{BASE_URL}/posts", json=data)
        if response.status_code == 200:
            result = response.json()
            post_data = result.get("data", {})
            print(f"✓ 成功发布帖子: {post_data.get('id')}")
            print(f"  内容: {post_data.get('content')}")
            return post_data.get("id")
        else:
            print(f"✗ 发布帖子失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None

def test_get_posts():
    """测试获取帖子列表"""
    print("\n6. 获取帖子列表...")
    try:
        response = requests.get(f"{BASE_URL}/posts")
        if response.status_code == 200:
            data = response.json()
            posts = data.get("data", [])
            print(f"✓ 成功获取 {len(posts)} 条帖子")
            for post in posts:
                author = post.get("author", {})
                print(f"  - {post.get('id')}: {post.get('content')[:30]}... (作者: {author.get('username')})")
            return posts
        else:
            print(f"✗ 获取帖子失败: {response.text}")
            return []
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return []

def test_get_comments(post_id):
    """测试获取评论"""
    print(f"\n7. 获取帖子 {post_id} 的评论...")
    try:
        # 等待一下让评论生成完成
        time.sleep(3)
        response = requests.get(f"{BASE_URL}/posts/{post_id}/comments")
        if response.status_code == 200:
            data = response.json()
            comments = data.get("data", [])
            print(f"✓ 成功获取 {len(comments)} 条评论")
            for i, comment in enumerate(comments[:3]):  # 只显示前3条
                author = comment.get("author", {})
                print(f"  {i+1}. {comment.get('content')[:30]}... (作者: {author.get('username')})")
            if len(comments) > 3:
                print(f"  ... 还有 {len(comments) - 3} 条评论")
            return comments
        else:
            print(f"✗ 获取评论失败: {response.text}")
            return []
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return []

def main():
    print("=" * 60)
    print("完整流程测试：设置用户 -> 发布帖子 -> 自动生成评论")
    print("=" * 60)
    
    # 1. 获取用户模板
    templates = test_get_user_templates()
    if not templates:
        print("无法获取用户模板，测试终止")
        return
    
    # 2. 选择第一个模板
    template = templates[0]
    template_name = template["name"]
    template_id = template["id"]
    
    # 3. 初始化AI用户
    if not test_init_ai_users(template_name):
        print("初始化AI用户失败，测试终止")
        return
    
    # 4. 设置当前用户
    user_id = test_set_current_user(template_id)
    if not user_id:
        print("设置当前用户失败，测试终止")
        return
    
    # 5. 验证当前用户
    test_get_current_user()
    
    # 6. 发布帖子
    post_id = test_create_post()
    if not post_id:
        print("发布帖子失败，测试终止")
        return
    
    # 7. 获取帖子列表
    test_get_posts()
    
    # 8. 等待并获取评论
    test_get_comments(post_id)
    
    print("\n" + "=" * 60)
    print("✓ 完整流程测试完成！")
    print("=" * 60)
    print("\n说明：")
    print("- 用户选择了模板后，系统自动创建了human_user")
    print("- 发布帖子时自动使用当前用户作为作者")
    print("- 发布帖子后，系统根据用户模板自动生成AI评论")
    print("- 整个过程通过WebSocket实时更新")

if __name__ == "__main__":
    main() 
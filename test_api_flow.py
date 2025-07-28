#!/usr/bin/env python3
"""
测试 InfluAI Backend API 完整流程
"""

import requests
import json
import time
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000"

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """发送HTTP请求"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def test_health_check():
    """测试健康检查"""
    print("1. 测试健康检查...")
    result = make_request("GET", "/health")
    if result:
        print(f"✓ 健康检查通过: {result}")
    else:
        print("✗ 健康检查失败")
    return result is not None

def test_get_user_templates():
    """测试获取用户模板"""
    print("\n2. 测试获取用户模板...")
    result = make_request("GET", "/user-templates")
    if result and result.get("code") == 200:
        templates = result.get("data", [])
        print(f"✓ 成功获取 {len(templates)} 个用户模板:")
        for template in templates:
            print(f"  - {template['name']}: {template['persona'][:50]}...")
        return templates
    else:
        print("✗ 获取用户模板失败")
        return []

def test_init_ai_users(template_name: str):
    """测试初始化AI用户"""
    print(f"\n3. 测试根据模板 '{template_name}' 初始化AI用户...")
    result = make_request("POST", f"/user-templates/{template_name}/init-ai-users")
    if result and result.get("code") == 200:
        print(f"✓ {result.get('message')}")
        return True
    else:
        print("✗ 初始化AI用户失败")
        return False

def test_create_post():
    """测试发布帖子"""
    print("\n4. 测试发布帖子...")
    post_content = "这是一条测试帖子，用来验证API功能是否正常。"
    data = {"content": post_content}
    result = make_request("POST", "/posts", data)
    if result and result.get("code") == 200:
        post = result.get("data")
        print(f"✓ 成功发布帖子: {post['content']}")
        print(f"  帖子ID: {post['id']}")
        return post
    else:
        print("✗ 发布帖子失败")
        return None

def test_get_posts():
    """测试获取帖子列表"""
    print("\n5. 测试获取帖子列表...")
    result = make_request("GET", "/posts")
    if result and result.get("code") == 200:
        posts = result.get("data", [])
        print(f"✓ 成功获取 {len(posts)} 条帖子")
        if posts:
            latest_post = posts[0]
            print(f"  最新帖子: {latest_post['content'][:30]}...")
        return posts
    else:
        print("✗ 获取帖子列表失败")
        return []

def test_like_post(post_id: str):
    """测试点赞帖子"""
    print(f"\n6. 测试点赞帖子 {post_id}...")
    result = make_request("POST", f"/posts/{post_id}/like")
    if result and result.get("code") == 200:
        like_data = result.get("data")
        print(f"✓ 成功点赞帖子，当前点赞数: {like_data['likes']}")
        return True
    else:
        print("✗ 点赞帖子失败")
        return False

def test_create_comment(post_id: str):
    """测试发布评论"""
    print(f"\n7. 测试为帖子 {post_id} 发布评论...")
    comment_content = "这是一条测试评论，用来验证评论功能。"
    data = {"content": comment_content}
    result = make_request("POST", f"/posts/{post_id}/comments", data)
    if result and result.get("code") == 200:
        comment = result.get("data")
        print(f"✓ 成功发布评论: {comment['content']}")
        print(f"  评论ID: {comment['id']}")
        return comment
    else:
        print("✗ 发布评论失败")
        return None

def test_get_comments(post_id: str):
    """测试获取评论列表"""
    print(f"\n8. 测试获取帖子 {post_id} 的评论列表...")
    result = make_request("GET", f"/posts/{post_id}/comments")
    if result and result.get("code") == 200:
        comments = result.get("data", [])
        print(f"✓ 成功获取 {len(comments)} 条评论")
        if comments:
            latest_comment = comments[0]
            print(f"  最新评论: {latest_comment['content'][:30]}...")
        return comments
    else:
        print("✗ 获取评论列表失败")
        return []

def test_like_comment(comment_id: str):
    """测试点赞评论"""
    print(f"\n9. 测试点赞评论 {comment_id}...")
    result = make_request("POST", f"/comments/{comment_id}/like")
    if result and result.get("code") == 200:
        like_data = result.get("data")
        print(f"✓ 成功点赞评论，当前点赞数: {like_data['likes']}")
        return True
    else:
        print("✗ 点赞评论失败")
        return False

def main():
    """主测试流程"""
    print("=" * 60)
    print("InfluAI Backend API 完整流程测试")
    print("=" * 60)
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 1. 健康检查
    if not test_health_check():
        print("服务器未启动，请先运行 python run_server.py")
        return
    
    # 2. 获取用户模板
    templates = test_get_user_templates()
    if not templates:
        print("无法获取用户模板，测试终止")
        return
    
    # 3. 选择第一个模板初始化AI用户
    template_name = templates[0]["name"]
    if not test_init_ai_users(template_name):
        print("初始化AI用户失败，测试终止")
        return
    
    # 4. 发布帖子
    post = test_create_post()
    if not post:
        print("发布帖子失败，测试终止")
        return
    
    post_id = post["id"]
    
    # 5. 获取帖子列表
    test_get_posts()
    
    # 6. 点赞帖子
    test_like_post(post_id)
    
    # 7. 发布评论
    comment = test_create_comment(post_id)
    if not comment:
        print("发布评论失败，测试终止")
        return
    
    comment_id = comment["id"]
    
    # 8. 获取评论列表
    test_get_comments(post_id)
    
    # 9. 点赞评论
    test_like_comment(comment_id)
    
    print("\n" + "=" * 60)
    print("✓ 所有测试完成！")
    print("=" * 60)
    print("\nAPI文档地址: http://localhost:8000/docs")
    print("可以访问上述地址查看完整的API文档")

if __name__ == "__main__":
    main() 
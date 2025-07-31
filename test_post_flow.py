#!/usr/bin/env python3
"""
测试发布帖子的完整流程
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_post_flow():
    """测试发布帖子的完整流程"""
    
    print("=== 测试发布帖子完整流程 ===")
    
    # 1. 获取所有人类用户
    print("\n1. 获取所有人类用户...")
    response = requests.get(f"{BASE_URL}/user/profile")
    if response.status_code != 200:
        print(f"获取用户失败: {response.status_code}")
        return
    
    users = response.json()["data"]
    if not users:
        print("没有找到用户，请先创建用户")
        return
    
    print(f"找到 {len(users)} 个用户:")
    for user in users:
        print(f"  - ID: {user['humanUserId']}, 用户名: {user['humanUsername']}, 模板ID: {user['userTemplateId']}")
    
    # 2. 设置当前用户
    print(f"\n2. 设置当前用户为: {users[0]['humanUsername']}")
    response = requests.post(f"{BASE_URL}/user/set-current", json={
        "human_user_id": users[0]["humanUserId"]
    })
    
    if response.status_code != 200:
        print(f"设置当前用户失败: {response.status_code}")
        return
    
    print("当前用户设置成功")
    
    # 3. 发布帖子
    print("\n3. 发布帖子...")
    post_content = "这是一条测试帖子，用来验证发布帖子的完整流程！"
    response = requests.post(f"{BASE_URL}/posts", json={
        "content": post_content
    })
    
    if response.status_code != 200:
        print(f"发布帖子失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        return
    
    post_data = response.json()["data"]
    print(f"帖子发布成功!")
    print(f"  帖子ID: {post_data['id']}")
    print(f"  内容: {post_data['content']}")
    print(f"  作者: {post_data['author']['username']}")
    print(f"  点赞数: {post_data['likes']}")
    print(f"  评论数: {post_data['commentsCount']}")
    
    post_id = post_data['id'].replace("post_", "")
    
    # 4. 等待评论生成
    print("\n4. 等待评论生成...")
    time.sleep(3)  # 等待3秒让评论生成
    
    # 5. 获取帖子评论
    print(f"\n5. 获取帖子 {post_id} 的评论...")
    response = requests.get(f"{BASE_URL}/posts/{post_id}/comments")
    
    if response.status_code != 200:
        print(f"获取评论失败: {response.status_code}")
        return
    
    comments_data = response.json()["data"]
    print(f"找到 {len(comments_data)} 条评论:")
    
    for i, comment in enumerate(comments_data[:5]):  # 只显示前5条
        print(f"  {i+1}. {comment['content']} (点赞: {comment['likes']})")
    
    if len(comments_data) > 5:
        print(f"  ... 还有 {len(comments_data) - 5} 条评论")
    
    # 6. 获取更新后的帖子信息
    print(f"\n6. 获取更新后的帖子信息...")
    response = requests.get(f"{BASE_URL}/posts")
    
    if response.status_code != 200:
        print(f"获取帖子列表失败: {response.status_code}")
        return
    
    posts = response.json()["data"]
    # 找到我们刚发布的帖子
    our_post = None
    for post in posts:
        if post['id'] == f"post_{post_id}":
            our_post = post
            break
    
    if our_post:
        print(f"更新后的帖子信息:")
        print(f"  点赞数: {our_post['likes']}")
        print(f"  评论数: {our_post['commentsCount']}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_post_flow() 
#!/usr/bin/env python3
"""
简化的API测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"健康检查: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_user_templates():
    """测试用户模板接口"""
    try:
        response = requests.get(f"{BASE_URL}/user-templates")
        print(f"用户模板: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"用户模板测试失败: {e}")
        return False

def test_create_post():
    """测试发布帖子"""
    try:
        data = {"content": "这是一条测试帖子"}
        response = requests.post(f"{BASE_URL}/posts", json=data)
        print(f"发布帖子: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data.get("data", {}).get("id")
        else:
            print(f"错误响应: {response.text}")
        return None
    except Exception as e:
        print(f"发布帖子失败: {e}")
        return None

def test_get_posts():
    """测试获取帖子列表"""
    try:
        response = requests.get(f"{BASE_URL}/posts")
        print(f"获取帖子: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取帖子失败: {e}")
        return False

def main():
    print("开始API测试...")
    
    # 1. 健康检查
    if not test_health():
        print("服务器未启动或健康检查失败")
        return
    
    # 2. 用户模板
    test_user_templates()
    
    # 3. 发布帖子
    post_id = test_create_post()
    
    # 4. 获取帖子列表
    test_get_posts()
    
    print("测试完成")

if __name__ == "__main__":
    main() 
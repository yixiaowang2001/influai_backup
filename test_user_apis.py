#!/usr/bin/env python3
"""
测试人类用户相关API接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_all_human_users():
    """测试获取所有人类用户"""
    print("1. 测试获取所有人类用户...")
    try:
        response = requests.get(f"{BASE_URL}/user/profile")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            users = data.get("data", [])
            print(f"✓ 成功获取 {len(users)} 个用户")
            return users
        else:
            print(f"✗ 请求失败: {response.text}")
            return []
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return []

def test_get_human_user_by_id(user_id: int):
    """测试获取特定人类用户"""
    print(f"\n2. 测试获取用户ID为 {user_id} 的用户...")
    try:
        response = requests.get(f"{BASE_URL}/user/profile/{user_id}")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            user = data.get("data", {})
            print(f"✓ 成功获取用户: {user.get('humanUsername')}")
            return user
        else:
            print(f"✗ 请求失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None

def test_get_nonexistent_user():
    """测试获取不存在的用户"""
    print(f"\n3. 测试获取不存在的用户...")
    try:
        response = requests.get(f"{BASE_URL}/user/profile/999")
        print(f"状态码: {response.status_code}")
        if response.status_code == 404:
            print(f"✓ 正确处理了不存在的用户: {response.json()}")
            return True
        else:
            print(f"✗ 预期404错误，但得到: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("人类用户API接口测试")
    print("=" * 60)
    
    # 1. 获取所有用户
    users = test_get_all_human_users()
    
    if users:
        # 2. 获取第一个用户
        first_user_id = users[0].get("humanUserId")
        if first_user_id:
            test_get_human_user_by_id(first_user_id)
    
    # 3. 测试不存在的用户
    test_get_nonexistent_user()
    
    print("\n" + "=" * 60)
    print("✓ 所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main() 
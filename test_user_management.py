#!/usr/bin/env python3
"""
测试用户管理功能：设置、获取、清除当前用户
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_all_users():
    """测试获取所有用户"""
    print("1. 获取所有人类用户...")
    try:
        response = requests.get(f"{BASE_URL}/user/profile")
        if response.status_code == 200:
            data = response.json()
            users = data.get("data", [])
            print(f"✓ 成功获取 {len(users)} 个用户")
            for user in users:
                print(f"  - ID: {user['humanUserId']}, 用户名: {user['humanUsername']}")
            return users
        else:
            print(f"✗ 获取用户失败: {response.text}")
            return []
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return []

def test_get_current_user():
    """测试获取当前用户"""
    print("\n2. 获取当前用户...")
    try:
        response = requests.get(f"{BASE_URL}/user/current")
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})
            print(f"✓ 当前用户: {user_data.get('humanUsername')} (ID: {user_data.get('humanUserId')})")
            return user_data
        elif response.status_code == 404:
            print("✓ 当前没有设置用户")
            return None
        else:
            print(f"✗ 获取当前用户失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None

def test_set_current_user_by_id(human_user_id):
    """测试通过ID设置当前用户"""
    print(f"\n3. 通过ID设置当前用户 (ID: {human_user_id})...")
    try:
        data = {"human_user_id": human_user_id}
        response = requests.post(f"{BASE_URL}/user/set-current", json=data)
        if response.status_code == 200:
            result = response.json()
            user_data = result.get("data", {})
            print(f"✓ 成功设置当前用户: {user_data.get('humanUsername')}")
            return user_data
        else:
            print(f"✗ 设置用户失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None



def test_clear_current_user():
    """测试清除当前用户"""
    print("\n5. 清除当前用户...")
    try:
        response = requests.delete(f"{BASE_URL}/user/current")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {data.get('message')}")
            return True
        else:
            print(f"✗ 清除用户失败: {response.text}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_switch_users():
    """测试切换用户"""
    print("\n6. 测试用户切换...")
    
    # 获取所有用户
    users = test_get_all_users()
    if len(users) < 2:
        print("需要至少2个用户来测试切换功能")
        return
    
    # 设置第一个用户
    user1 = users[0]
    test_set_current_user_by_id(user1['humanUserId'])
    test_get_current_user()
    
    # 切换到第二个用户
    user2 = users[1]
    test_set_current_user_by_id(user2['humanUserId'])
    test_get_current_user()
    
    # 切换回第一个用户
    test_set_current_user_by_id(user1['humanUserId'])
    test_get_current_user()

def main():
    print("=" * 60)
    print("用户管理功能测试")
    print("=" * 60)
    
    # 1. 获取所有用户
    users = test_get_all_users()
    if not users:
        print("无法获取用户列表，测试终止")
        return
    
    # 2. 检查当前用户状态
    test_get_current_user()
    
    # 3. 通过ID设置当前用户
    if users:
        test_set_current_user_by_id(users[0]['humanUserId'])
        test_get_current_user()
    

    
    # 5. 测试用户切换
    test_switch_users()
    
    # 6. 清除当前用户
    test_clear_current_user()
    test_get_current_user()
    
    print("\n" + "=" * 60)
    print("✓ 用户管理功能测试完成！")
    print("=" * 60)
    print("\n说明：")
    print("- 同时只能有一个当前用户")
    print("- 设置新用户会覆盖之前的用户")
    print("- 通过用户ID来设置用户")

if __name__ == "__main__":
    main() 
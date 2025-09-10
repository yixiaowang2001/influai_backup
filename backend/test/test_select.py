#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI 评论筛选测试脚本

功能：
- 从数据库获取评论数据
- 基于态度和长度系数筛选重要评论
- 支持不同层级的评论筛选
- 提供详细的测试和统计功能

使用方法：
1. 确保已配置好数据库和API密钥
2. 运行脚本：python test_lvn.py
3. 观察评论筛选过程和结果
"""

import math
import os
import sys
from typing import List, Tuple, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

from backend.models import Attitude
from backend.database.database import get_db
from backend.database import crud
from backend.database import models


def get_comments_from_database(post_id: int, parent_comment_id: Optional[int] = None) -> List[Tuple[str, Attitude]]:
    """
    从数据库获取评论数据
    
    参数:
        post_id: 帖子ID（必填）
        parent_comment_id: 父评论ID（可选，为空则获取一级评论，不为空则获取子评论）
    
    返回:
        评论列表 [(评论内容, 态度)]
    """
    db = next(get_db())
    comments = []

    try:
        if parent_comment_id is None:
            # 获取帖子下的一级评论
            db_comments = crud.get_comments_by_post(db, post_id)
            db_comments = [c for c in db_comments if c.comment_level == 1]
        else:
            # 获取指定父评论下的子评论
            db_comments = db.query(models.Comment).filter(
                models.Comment.post_id == post_id,
                models.Comment.master_comment_id == parent_comment_id
            ).all()

        for comment in db_comments:
            content = comment.comment_content
            attitude = None

            if comment.sender_type == 'ai_user':
                # 从AI用户获取态度值
                ai_user = db.query(models.AIUser).filter(
                    models.AIUser.user_id == comment.sender_id
                ).first()
                if ai_user:
                    attitude = Attitude.from_value(ai_user.attitude_value)
            else:
                # 人类用户，使用默认的中立态度
                attitude = Attitude.NEUTRAL

            if attitude:
                comments.append((content, attitude))

    except Exception as e:
        print(f"数据库查询错误: {e}")
    finally:
        db.close()

    return comments


def get_attitude_coefficient(attitude: Attitude) -> float:
    """根据态度计算系数"""
    attitude_coeff_map = {
        Attitude.BAD: 0.9,  # 极差态度 - 最高系数
        Attitude.PERFECT: 0.7,  # 狂热态度 - 高系数
        Attitude.GOOD: 0.5,  # 极好态度 - 中等系数
        Attitude.NEUTRAL_NEGATIVE: 0.6,  # 不友善态度 - 高系数
        Attitude.NEUTRAL: 0.3,  # 中立态度 - 中等系数
        Attitude.NEUTRAL_POSITIVE: 0.1  # 友善态度 - 低系数
    }
    return attitude_coeff_map.get(attitude, 0.1)


def get_length_coefficient(comment: str) -> float:
    """
    根据评论长度计算系数
    
    评论越长，系数越高，但20字后权重增加量递减
    使用分段函数实现递减增长
    """
    length = len(comment)

    # 长度系数范围: 0.5 - 1.8
    if length <= 10:
        return 0.5
    elif length <= 20:
        # 10-20字符：线性增长 0.5-1.0
        return 0.5 + (length - 10) * 0.5 / 10
    elif length <= 50:
        # 20-50字符：递减增长 1.0-1.4
        progress = (length - 20) / 30
        return 1.0 + 0.4 * math.sqrt(progress)
    else:
        # 50字符以上：极缓慢增长 1.4-1.8
        return 1.4 + 0.4 * math.log(length - 49) / math.log(200)


def filter_important_comments_from_db(post_id: int, parent_comment_id: Optional[int] = None, filter_count: int = 10) -> \
        List[Tuple[str, float, Attitude]]:
    """
    从数据库筛选重要评论
    
    参数:
        post_id: 帖子ID（必填）
        parent_comment_id: 父评论ID（可选，为空则处理一级评论，不为空则处理子评论）
        filter_count: 筛选数量（可选，默认为10）
    
    返回:
        筛选出来的评论列表，按系数排序 [(评论内容, 综合系数, 态度)]
    """
    # 从数据库获取评论数据
    comments_data = get_comments_from_database(post_id, parent_comment_id)

    if not comments_data:
        print(f"未找到评论数据 - 帖子ID: {post_id}, 父评论ID: {parent_comment_id}")
        return []

    # 将评论按态度分类
    attitude_comments = Attitude.create_dict()
    for content, attitude in comments_data:
        attitude_comments[attitude].append(content)

    # 计算总评论数
    total_comments = len(comments_data)
    target_count = min(filter_count, total_comments)

    print(f"数据库查询结果 - 帖子ID: {post_id}, 父评论ID: {parent_comment_id}")
    print(f"总评论数: {total_comments}, 目标筛选数: {target_count}")

    # 计算每个评论的综合系数
    comment_scores = []

    for attitude, comments in attitude_comments.items():
        if not comments:
            continue

        attitude_coeff = get_attitude_coefficient(attitude)

        for comment in comments:
            length_coeff = get_length_coefficient(comment)
            combined_score = attitude_coeff * length_coeff
            comment_scores.append((comment, combined_score, attitude))

    # 按综合系数降序排序
    comment_scores.sort(key=lambda x: x[1], reverse=True)

    return comment_scores[:target_count]


def print_all_comments(post_id: int, parent_comment_id: Optional[int] = None):
    """打印所有评论内容"""
    print("=== 打印所有评论内容 ===")
    print(f"帖子ID: {post_id}")
    print(f"父评论ID: {parent_comment_id if parent_comment_id else '无（一级评论）'}")

    comments_data = get_comments_from_database(post_id, parent_comment_id)

    if not comments_data:
        print("未找到评论数据")
        return []

    print(f"\n总评论数: {len(comments_data)}")
    print("-" * 80)

    # 按态度分组显示
    attitude_groups = {}
    for content, attitude in comments_data:
        if attitude not in attitude_groups:
            attitude_groups[attitude] = []
        attitude_groups[attitude].append(content)

    for attitude, comments in attitude_groups.items():
        print(f"\n[{str(attitude):8s}] 态度 ({len(comments)} 条):")
        for i, comment in enumerate(comments, 1):
            print(f"  {i:2d}. {comment}")

    return comments_data


def test_filter_comments_from_db(post_id: int, parent_comment_id: Optional[int] = None, filter_count: int = 10):
    """测试从数据库筛选重要评论功能"""
    print("=== 测试从数据库筛选重要评论功能 ===")
    print(f"帖子ID: {post_id}")
    print(f"父评论ID: {parent_comment_id if parent_comment_id else '无（一级评论）'}")
    print(f"筛选数量: {filter_count}")

    # 执行筛选
    filtered_comments = filter_important_comments_from_db(post_id, parent_comment_id, filter_count)

    if not filtered_comments:
        print("未找到符合条件的评论数据")
        return []

    print(f"\n筛选出 {len(filtered_comments)} 条重要评论:")
    print("-" * 80)

    for i, (comment, score, attitude) in enumerate(filtered_comments, 1):
        print(f"{i:2d}. [{str(attitude):8s}] 系数:{score:.3f} | {comment}")

    # 统计各态度的筛选结果
    attitude_counts = {}
    for _, _, attitude in filtered_comments:
        attitude_counts[attitude] = attitude_counts.get(attitude, 0) + 1

    print(f"\n各态度筛选结果统计:")
    for attitude, count in attitude_counts.items():
        print(f"  {str(attitude):8s}: {count} 条")

    return filtered_comments


def test_coefficients():
    """测试系数算法"""
    print("=== 测试系数算法 ===")

    # 测试态度系数
    print("\n态度系数:")
    attitudes = [Attitude.BAD, Attitude.NEUTRAL_NEGATIVE, Attitude.PERFECT,
                 Attitude.GOOD, Attitude.NEUTRAL, Attitude.NEUTRAL_POSITIVE]
    for attitude in attitudes:
        coeff = get_attitude_coefficient(attitude)
        print(f"  {str(attitude):8s}: {coeff:.3f}")

    # 测试长度系数
    print("\n长度系数测试:")
    test_comments = [
        "短评论",  # 3字
        "这是一个中等长度的评论内容",  # 12字
        "这是一个比较长的评论内容，用来测试20字左右的长度系数计算效果",  # 25字
        "这是一个非常长的评论内容，用来测试50字左右的长度系数计算效果，看看递减增长是否正常工作",  # 35字
        "这是一个超级长的评论内容，用来测试50字以上的长度系数计算效果，看看递减增长是否正常工作，以及极缓慢增长的效果如何，这个评论应该超过50个字符"
        # 60字
    ]

    for comment in test_comments:
        length = len(comment)
        coeff = get_length_coefficient(comment)
        print(f"  长度: {length:2d}字, 系数: {coeff:.3f}, 内容: {comment[:20]}...")

    print("\n=== 筛选机制说明 ===")
    print("评论筛选完全基于综合系数排序（态度系数 × 长度系数）")
    print("极差评论系数：0.9（最高权重）")
    print("不友善评论系数：0.6（高权重）")
    print("狂热评论系数：0.7（高权重）")
    print("极好评论系数：0.5（中等权重）")
    print("中立评论系数：0.3（低权重）")
    print("友善评论系数：0.1（最低权重）")


if __name__ == "__main__":
    # 设置数据库密码环境变量
    os.environ["MYSQL_PASSWORD"] = "influai"

    # 测试系数算法
    test_coefficients()

    print("\n" + "=" * 80 + "\n")

    # 打印所有评论内容
    print_all_comments(post_id=1)

    print("\n" + "=" * 80 + "\n")

    # 测试筛选算法
    test_filter_comments_from_db(post_id=1, filter_count=10)

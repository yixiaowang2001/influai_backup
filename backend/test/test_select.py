#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI 评论筛选测试脚本

功能：
- 从数据库获取评论数据
- 基于态度权重与长度钟形系数筛选重要评论
- 支持不同层级的评论筛选
- 提供详细的测试和统计功能

使用方法：
1. 确保已配置好数据库和API密钥
2. 运行脚本：python backend/test/test_select.py
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


# 长度钟形系数（10-50字最佳）
def get_length_bell_coefficient(comment: str) -> float:
    L = len(comment)
    peak = 1.4
    floor = 0.6
    center = 30.0
    sigma = 14.0
    bell = math.exp(-((L - center) ** 2) / (2 * sigma * sigma))
    return floor + (peak - floor) * bell


# 统一态度权重（与平台观感更接近，可按需调整）
ATTITUDE_WEIGHT = {
    Attitude.BAD: 0.80,  # 极差
    Attitude.NEUTRAL_NEGATIVE: 0.65,  # 不友善
    Attitude.PERFECT: 0.62,  # 狂热
    Attitude.GOOD: 0.60,  # 极好
    Attitude.NEUTRAL_POSITIVE: 0.58,  # 友善
    Attitude.NEUTRAL: 0.55,  # 中立
}


def get_attitude_weight(attitude: Attitude) -> float:
    return ATTITUDE_WEIGHT.get(attitude, 0.55)


# 整体评分方法（态度×钟形长度）
def compute_comment_score(comment: str, attitude: Attitude) -> float:
    attitude_coeff = get_attitude_weight(attitude)
    length_coeff = get_length_bell_coefficient(comment)
    return attitude_coeff * length_coeff


# 态度配额筛选（限制负向情绪占比）
def select_with_attitude_quota(
        items: List[Tuple[str, float, Attitude]],
        k: int,
        max_negative_ratio: float = 0.4,
) -> List[Tuple[str, float, Attitude]]:
    # 定义“负向/强烈”集合：极差、不友善、狂热
    negative_set = {Attitude.BAD, Attitude.NEUTRAL_NEGATIVE, Attitude.PERFECT}

    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    selected: List[Tuple[str, float, Attitude]] = []

    negative_cap = int(k * max_negative_ratio)
    negative_used = 0

    for content, score, attitude in items_sorted:
        if len(selected) >= k:
            break
        if attitude in negative_set:
            if negative_used >= negative_cap:
                continue
            negative_used += 1
        selected.append((content, score, attitude))

    # 若不足k，可放宽：这里简单回填剩余（不再区分配额）
    if len(selected) < k:
        for content, score, attitude in items_sorted:
            if len(selected) >= k:
                break
            if (content, score, attitude) in selected:
                continue
            selected.append((content, score, attitude))

    return selected


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

    # 计算每条评论的综合分
    comment_scores: List[Tuple[str, float, Attitude]] = []
    for content, attitude in comments_data:
        score = compute_comment_score(content, attitude)
        comment_scores.append((content, score, attitude))

    # 先整体排序，再做态度配额约束选择
    selected = select_with_attitude_quota(comment_scores, k=min(filter_count, len(comment_scores)))
    return selected


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

    # 测试态度权重
    print("\n态度权重:")
    attitudes = [Attitude.BAD, Attitude.NEUTRAL_NEGATIVE, Attitude.PERFECT,
                 Attitude.GOOD, Attitude.NEUTRAL, Attitude.NEUTRAL_POSITIVE]
    for attitude in attitudes:
        coeff = get_attitude_weight(attitude)
        print(f"  {str(attitude):8s}: {coeff:.3f}")

    # 测试长度钟形系数
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
        coeff = get_length_bell_coefficient(comment)
        print(f"  长度: {length:2d}字, 系数: {coeff:.3f}, 内容: {comment[:20]}...")

    print("\n=== 筛选机制说明 ===")
    print("评论筛选基于综合分排序（统一态度权重 × 钟形长度系数[10-50字最佳]）+ 态度配额约束")


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
    test_filter_comments_from_db(post_id=1, filter_count=5)

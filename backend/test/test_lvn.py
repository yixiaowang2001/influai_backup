#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI LVN评论生成测试脚本 - 深度优先自我问答方案

基于第三个方案：深度优先自我问答方案
通过一次大模型调用，模拟所有用户角色，直接生成完整的评论对话链

使用方法：
1. 确保已配置好数据库和API密钥
2. 运行脚本：python test_lvn.py
3. 观察LVN评论生成过程和结果

功能：
- 测试深度优先自我问答方案的LVN评论生成
- 支持热度分数计算和热门评论筛选
- 支持多角色模拟和对话连贯性
- 显示详细的生成过程和统计信息
"""

import os
import sys
from typing import List, Tuple, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..models import Attitude
from ..database.database import get_db
from ..database import crud
from ..database import models


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
            # 过滤出一级评论（comment_level=1）
            db_comments = [c for c in db_comments if c.comment_level == 1]
        else:
            # 获取指定父评论下的子评论
            db_comments = db.query(models.Comment).filter(
                models.Comment.post_id == post_id,
                models.Comment.master_comment_id == parent_comment_id
            ).all()

        for comment in db_comments:
            # 获取评论内容
            content = comment.comment_content

            # 获取态度信息
            attitude = None
            if comment.sender_type == 'ai_user':
                # 从AI用户获取态度值
                ai_user = db.query(models.AIUser).filter(
                    models.AIUser.user_id == comment.sender_id
                ).first()
                if ai_user:
                    attitude = Attitude.from_value(ai_user.attitude_value)
            else:
                # 人类用户，使用comment_user_type作为态度
                # 这里需要根据实际的comment_user_type到Attitude的映射关系来转换
                # 暂时使用默认的中立态度
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
    从数据库筛选同层级重要评论
    
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
        if not comments:  # 跳过空的态度分类
            continue

        # 系数1：根据态度决定
        attitude_coeff = get_attitude_coefficient(attitude)

        for comment in comments:
            # 系数2：根据评论长度决定
            length_coeff = get_length_coefficient(comment)

            # 综合系数 = 态度系数 * 长度系数
            combined_score = attitude_coeff * length_coeff

            comment_scores.append((comment, combined_score, attitude))

    # 按综合系数降序排序
    comment_scores.sort(key=lambda x: x[1], reverse=True)

    # 返回筛选结果
    return comment_scores[:target_count]


def get_attitude_coefficient(attitude: Attitude) -> float:
    """
    根据态度计算系数1
    
    极端态度(BAD、PERFECT、GOOD): 0.8-0.9
    中立: 0.3
    友善、不友善: 0.1
    """
    attitude_coeff_map = {
        Attitude.BAD: 0.9,  # 极差态度 - 最高系数
        Attitude.PERFECT: 0.85,  # 狂热态度 - 高系数
        Attitude.GOOD: 0.8,  # 极好态度 - 高系数
        Attitude.NEUTRAL: 0.3,  # 中立态度 - 中等系数
        Attitude.NEUTRAL_POSITIVE: 0.1,  # 友善态度 - 低系数
        Attitude.NEUTRAL_NEGATIVE: 0.1  # 不友善态度 - 低系数
    }
    return attitude_coeff_map.get(attitude, 0.1)


def get_length_coefficient(comment: str) -> float:
    """
    根据评论长度计算系数2
    
    评论越长，系数越高
    使用对数函数平滑增长
    """
    length = len(comment)

    # 使用对数函数，避免过长评论系数过高
    # 长度系数范围: 0.5 - 1.5
    if length <= 10:
        return 0.5
    elif length <= 50:
        # 10-50字符：线性增长 0.5-1.0
        return 0.5 + (length - 10) * 0.5 / 40
    else:
        # 50字符以上：对数增长 1.0-1.5
        import math
        return 1.0 + 0.5 * math.log(length - 49) / math.log(100)


def print_all_comments(post_id: int, parent_comment_id: Optional[int] = None):
    """
    打印所有评论内容
    
    参数:
        post_id: 帖子ID（必填）
        parent_comment_id: 父评论ID（可选，为空则打印一级评论，不为空则打印子评论）
    """
    print("=== 打印所有评论内容 ===")
    print(f"帖子ID: {post_id}")
    print(f"父评论ID: {parent_comment_id if parent_comment_id else '无（一级评论）'}")
    
    # 从数据库获取评论数据
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
    """
    测试从数据库筛选重要评论功能
    
    参数:
        post_id: 帖子ID（必填）
        parent_comment_id: 父评论ID（可选）
        filter_count: 筛选数量（可选，默认为10）
    """
    print("=== 测试从数据库筛选同层级重要评论功能 ===")
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


if __name__ == "__main__":
    # 设置数据库密码环境变量
    import os
    os.environ["MYSQL_PASSWORD"] = "influai"

    # 打印所有评论内容
    print_all_comments(post_id=1)
    
    print("\n" + "="*80 + "\n")
    
    # 测试数据库筛选功能
    # 示例：测试帖子ID为1的一级评论筛选
    test_filter_comments_from_db(post_id=1, filter_count=10)

    # 示例：测试帖子ID为1，父评论ID为1的子评论筛选（测试无子评论的情况）
    test_filter_comments_from_db(post_id=1, parent_comment_id=1, filter_count=3)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI 快速测试脚本

无需交互，直接使用本地变量进行测试
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_module.post_related import predict_post_stats
from backend.ai_module.comment_related import (
    generate_lv1_seeds,
    expand_lv1_comments,
    predict_comment_likes
)
from backend.services.post_service import PostService
from backend.database.database import get_db
from backend.database.crud import get_all_user_templates, create_human_user
from backend.models import Attitude
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def quick_test():
    """快速测试函数"""
    
    # ==================== 测试配置 ====================
    # 在这里修改测试参数
    TEMPLATE_ID = 1  # 模板ID，1=STAR, 2=INFLUENCER, 3=CASTER
    POST_CONTENT = "今天天气真好，心情也很棒！"  # 测试帖子内容
    
    print(" InfluAI 快速测试开始")
    print("="*60)
    print(f" 测试帖子: {POST_CONTENT}")
    print(f" 模板ID: {TEMPLATE_ID}")
    print("="*60)
    
    try:
        # 获取数据库连接
        db = next(get_db())
        
        # 1. 加载用户模板
        print("\n1. 加载用户模板...")
        templates = get_all_user_templates(db)
        if not templates:
            print(" 没有找到用户模板")
            return False
            
        template = next((t for t in templates if t.template_id == TEMPLATE_ID), None)
        if not template:
            print(f" 没有找到ID为 {TEMPLATE_ID} 的模板")
            return False
            
        print(f" 找到模板: {template.template_name}")
        print(f"    人设: {template.persona[:100]}...")
        print(f"    粉丝数: {template.follower_count}")
        
        # 2. 创建测试用户
        print("\n2. 创建测试用户...")
        import time
        username = f"测试用户_{int(time.time())}"
        human_user = create_human_user(
            db=db,
            username=username,
            user_template_id=TEMPLATE_ID,
            avatar_path=""
        )
        print(f" 创建用户: {username} (ID: {human_user.user_id})")
        
        # 3. 测试帖子统计预测
        print("\n3. 测试帖子统计预测...")
        history_posts = ["昨天的工作很充实！", "新项目进展顺利", "感谢大家的支持"]
        
        stats = predict_post_stats(
            persona=template.persona,
            follower_count=template.follower_count,
            post_content=POST_CONTENT,
            history_posts=history_posts,
            retry=3
        )
        
        print(f" 预测结果:")
        print(f"   新增粉丝数: {stats['pred_new_follower_count']}")
        print(f"   评论总数: {stats['pred_comment_count']}")
        print(f"   点赞总数: {stats['pred_like_count']}")
        
        # 4. 测试种子评论生成
        print("\n4. 测试种子评论生成...")
        seeds = generate_lv1_seeds(
            persona=template.persona,
            post_content=POST_CONTENT,
            history_posts=history_posts,
            retry=3
        )
        
        print(f" 种子评论生成结果:")
        total_seeds = 0
        for attitude, comments in seeds.items():
            if comments:
                print(f"   {attitude.value} ({len(comments)}条):")
                for i, comment in enumerate(comments, 1):
                    print(f"     {i}. {comment}")
                    total_seeds += 1
        
        print(f" 总计生成 {total_seeds} 条种子评论")
        
        # 5. 测试评论扩展
        print("\n5. 测试评论扩展...")
        total_expanded = 0
        
        for attitude, comments in seeds.items():
            if not comments:
                continue
                
            print(f"    扩展 {attitude.value} 态度评论:")
            seed_comment = comments[0]
            
            expanded = expand_lv1_comments(
                persona=template.persona,
                post_content=POST_CONTENT,
                attitude_type=attitude,
                seed_comments=[seed_comment],
                expand_count=3,
                retry=3
            )
            
            print(f"     扩展结果 ({len(expanded)}条):")
            for i, comment in enumerate(expanded, 1):
                print(f"       {i}. {comment}")
                total_expanded += 1
        
        print(f" 总计扩展 {total_expanded} 条评论")
        
        # 6. 测试点赞数预测
        print("\n6. 测试点赞数预测...")
        predictions = []
        for i in range(5):
            likes = predict_comment_likes(
                follower_count=template.follower_count,
                float_range=0.9,
                zoom_index=0.01
            )
            predictions.append(likes)
        
        print(f" 点赞数预测结果:")
        for i, likes in enumerate(predictions, 1):
            print(f"   预测 {i}: {likes} 个赞")
        
        avg_likes = sum(predictions) / len(predictions)
        print(f" 平均点赞数: {avg_likes:.1f}")
        
        # 7. 测试完整帖子服务
        print("\n7. 测试完整帖子服务...")
        post_service = PostService(
            content=POST_CONTENT,
            template_id=TEMPLATE_ID,
            human_user_id=human_user.user_id,
            db=db
        )
        
        post_service.basic_update()
        
        print(f" 帖子服务结果:")
        print(f"   预测点赞数: {post_service.post.like_count}")
        print(f"   预测评论数: {post_service.pred_comment_count}")
        print(f"   新增粉丝数: {post_service.new_follower_count}")
        
        print(f"\n 种子评论结构:")
        if post_service.lv1_seeds:
            for attitude, comment_groups in post_service.lv1_seeds.items():
                print(f"   {attitude.value}:")
                for i, group in enumerate(comment_groups):
                    print(f"     组{i+1}: {group}")
        
        print("\n 所有测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f" 测试失败: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n 快速测试成功完成！")
    else:
        print("\n 快速测试失败")

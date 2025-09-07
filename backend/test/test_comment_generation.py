#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI 评论生成逻辑测试脚本

使用方法：
1. 确保已配置好数据库和API密钥
2. 运行脚本：python test_comment_generation.py
3. 按提示选择用户模板和输入帖子内容
4. 观察评论生成过程和结果

功能：
- 测试所有评论生成相关的方法
- 支持用户选择人物模板
- 支持自定义帖子内容
- 显示详细的生成过程和统计信息
"""

import sys
import os
import json
from typing import Dict, List, Optional

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
from backend.database.crud import get_all_user_templates, create_human_user, get_human_user_by_id
from backend.models import Attitude
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CommentGenerationTester:
    """评论生成测试器"""
    
    def __init__(self, template_id=None, post_content=None):
        self.db = next(get_db())
        self.user_templates = []
        self.current_human_user = None
        
        # 测试配置 - 可以通过参数或直接修改这些变量
        self.template_id = template_id
        self.post_content = post_content or "今天天气真好，心情也很棒！"
        
    def load_user_templates(self):
        """加载用户模板"""
        try:
            self.user_templates = get_all_user_templates(self.db)
            logger.info(f"成功加载 {len(self.user_templates)} 个用户模板")
            return True
        except Exception as e:
            logger.error(f"加载用户模板失败: {e}")
            return False
    
    def display_templates(self):
        """显示可用的用户模板"""
        print("\n" + "="*60)
        print("📋 可用的用户模板:")
        print("="*60)
        
        for i, template in enumerate(self.user_templates, 1):
            print(f"{i}. {template.template_name}")
            print(f"   📝 人设: {template.persona[:100]}...")
            print(f"   👥 粉丝数: {template.follower_count}")
            print(f"   📊 评论者分布: {json.dumps(template.commenter_distribution, ensure_ascii=False, indent=6)}")
            print("-" * 60)
    
    def select_template(self) -> Optional[int]:
        """选择用户模板"""
        if self.template_id:
            # 如果已经指定了template_id，直接使用
            selected_template = next((t for t in self.user_templates if t.template_id == self.template_id), None)
            if selected_template:
                print(f"✅ 使用指定模板: {selected_template.template_name}")
                return self.template_id
            else:
                print(f"❌ 指定的模板ID {self.template_id} 不存在")
                return None
        
        # 如果没有指定template_id，使用第一个模板
        if self.user_templates:
            selected_template = self.user_templates[0]
            print(f"✅ 使用默认模板: {selected_template.template_name}")
            return selected_template.template_id
        else:
            print("❌ 没有可用的用户模板")
            return None
    
    def get_post_content(self) -> Optional[str]:
        """获取帖子内容"""
        print("\n" + "="*60)
        print("📝 帖子内容:")
        print("="*60)
        
        if not self.post_content:
            print("❌ 帖子内容不能为空")
            return None
            
        if len(self.post_content) > 140:
            print("❌ 帖子内容不能超过140个字符")
            return None
            
        print(f"✅ 帖子内容: {self.post_content}")
        return self.post_content
    
    def create_test_user(self, template_id: int) -> Optional[int]:
        """创建测试用户"""
        try:
            # 生成唯一的用户名
            import time
            username = f"测试用户_{int(time.time())}"
            
            # 创建人类用户
            human_user = create_human_user(
                db=self.db,
                username=username,
                user_template_id=template_id,
                avatar_path=""
            )
            
            print(f"✅ 创建测试用户: {username} (ID: {human_user.user_id})")
            self.current_human_user = human_user
            return human_user.user_id
            
        except Exception as e:
            logger.error(f"创建测试用户失败: {e}")
            print(f"❌ 创建测试用户失败: {e}")
            return None
    
    def test_post_stats_prediction(self, template_id: int, post_content: str):
        """测试帖子统计数据预测"""
        print("\n" + "="*60)
        print("🔮 测试帖子统计数据预测")
        print("="*60)
        
        try:
            template = next(t for t in self.user_templates if t.template_id == template_id)
            
            # 模拟历史帖子
            history_posts = [
                "昨天的工作很充实！",
                "新项目进展顺利",
                "感谢大家的支持"
            ]
            
            print(f"📊 预测参数:")
            print(f"   人设: {template.persona[:50]}...")
            print(f"   粉丝数: {template.follower_count}")
            print(f"   帖子内容: {post_content}")
            print(f"   历史帖子: {history_posts}")
            
            # 调用预测方法
            stats = predict_post_stats(
                persona=template.persona,
                follower_count=template.follower_count,
                post_content=post_content,
                history_posts=history_posts,
                retry=3
            )
            
            print(f"\n📈 预测结果:")
            print(f"   新增粉丝数: {stats['pred_new_follower_count']}")
            print(f"   评论总数: {stats['pred_comment_count']}")
            print(f"   点赞总数: {stats['pred_like_count']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"帖子统计预测失败: {e}")
            print(f"❌ 帖子统计预测失败: {e}")
            return None
    
    def test_lv1_seeds_generation(self, template_id: int, post_content: str):
        """测试一级种子评论生成"""
        print("\n" + "="*60)
        print("🌱 测试一级种子评论生成")
        print("="*60)
        
        try:
            template = next(t for t in self.user_templates if t.template_id == template_id)
            
            # 模拟历史帖子
            history_posts = [
                "昨天的工作很充实！",
                "新项目进展顺利",
                "感谢大家的支持"
            ]
            
            print(f"📝 生成参数:")
            print(f"   人设: {template.persona[:50]}...")
            print(f"   帖子内容: {post_content}")
            
            # 调用种子评论生成方法
            seeds = generate_lv1_seeds(
                persona=template.persona,
                post_content=post_content,
                history_posts=history_posts,
                retry=3
            )
            
            print(f"\n🌱 种子评论生成结果:")
            total_seeds = 0
            for attitude, comments in seeds.items():
                print(f"\n   {attitude.value} ({len(comments)}条):")
                for i, comment in enumerate(comments, 1):
                    print(f"     {i}. {comment}")
                    total_seeds += 1
            
            print(f"\n📊 总计生成 {total_seeds} 条种子评论")
            return seeds
            
        except Exception as e:
            logger.error(f"种子评论生成失败: {e}")
            print(f"❌ 种子评论生成失败: {e}")
            return None
    
    def test_comment_expansion(self, template_id: int, post_content: str, seeds: Dict):
        """测试评论扩展"""
        print("\n" + "="*60)
        print("🔄 测试评论扩展")
        print("="*60)
        
        try:
            template = next(t for t in self.user_templates if t.template_id == template_id)
            
            total_expanded = 0
            
            for attitude, comments in seeds.items():
                if not comments:
                    continue
                    
                print(f"\n📝 扩展 {attitude.value} 态度评论:")
                print(f"   原始种子: {comments}")
                
                # 选择第一条评论作为扩展种子
                seed_comment = comments[0] if comments else "默认评论"
                
                # 调用扩展方法
                expanded = expand_lv1_comments(
                    persona=template.persona,
                    post_content=post_content,
                    attitude_type=attitude,
                    seed_comments=[seed_comment],
                    expand_count=3,
                    retry=3
                )
                
                print(f"   扩展结果 ({len(expanded)}条):")
                for i, comment in enumerate(expanded, 1):
                    print(f"     {i}. {comment}")
                    total_expanded += 1
            
            print(f"\n📊 总计扩展 {total_expanded} 条评论")
            return True
            
        except Exception as e:
            logger.error(f"评论扩展失败: {e}")
            print(f"❌ 评论扩展失败: {e}")
            return False
    
    def test_comment_likes_prediction(self, template_id: int):
        """测试评论点赞数预测"""
        print("\n" + "="*60)
        print("👍 测试评论点赞数预测")
        print("="*60)
        
        try:
            template = next(t for t in self.user_templates if t.template_id == template_id)
            
            print(f"📊 预测参数:")
            print(f"   粉丝数: {template.follower_count}")
            print(f"   浮动范围: 0.9")
            print(f"   缩放指数: 0.01")
            
            # 生成多个预测结果
            predictions = []
            for i in range(5):
                likes = predict_comment_likes(
                    follower_count=template.follower_count,
                    float_range=0.9,
                    zoom_index=0.01
                )
                predictions.append(likes)
            
            print(f"\n👍 点赞数预测结果:")
            for i, likes in enumerate(predictions, 1):
                print(f"   预测 {i}: {likes} 个赞")
            
            avg_likes = sum(predictions) / len(predictions)
            print(f"\n📊 平均点赞数: {avg_likes:.1f}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"点赞数预测失败: {e}")
            print(f"❌ 点赞数预测失败: {e}")
            return None
    
    def test_post_service(self, template_id: int, post_content: str, human_user_id: int):
        """测试完整的帖子服务"""
        print("\n" + "="*60)
        print("🚀 测试完整的帖子服务")
        print("="*60)
        
        try:
            print(f"📝 服务参数:")
            print(f"   模板ID: {template_id}")
            print(f"   帖子内容: {post_content}")
            print(f"   人类用户ID: {human_user_id}")
            
            # 创建帖子服务实例
            post_service = PostService(
                content=post_content,
                template_id=template_id,
                human_user_id=human_user_id,
                db=self.db
            )
            
            print(f"\n🔮 执行基础更新...")
            post_service.basic_update()
            
            print(f"📊 基础更新结果:")
            print(f"   预测点赞数: {post_service.post.like_count}")
            print(f"   预测评论数: {post_service.pred_comment_count}")
            print(f"   新增粉丝数: {post_service.new_follower_count}")
            
            print(f"\n🌱 种子评论:")
            if post_service.lv1_seeds:
                for attitude, comment_groups in post_service.lv1_seeds.items():
                    print(f"   {attitude.value}:")
                    for i, group in enumerate(comment_groups):
                        print(f"     组{i+1}: {group}")
            
            print(f"\n✅ 帖子服务测试完成")
            return post_service
            
        except Exception as e:
            logger.error(f"帖子服务测试失败: {e}")
            print(f"❌ 帖子服务测试失败: {e}")
            return None
    
    def run_full_test(self):
        """运行完整测试"""
        print("🎯 InfluAI 评论生成逻辑测试")
        print("="*60)
        
        # 1. 加载用户模板
        if not self.load_user_templates():
            return False
        
        # 2. 显示模板选择
        self.display_templates()
        
        # 3. 选择模板
        template_id = self.select_template()
        if not template_id:
            return False
        
        # 4. 获取帖子内容
        post_content = self.get_post_content()
        if not post_content:
            return False
        
        # 5. 创建测试用户
        human_user_id = self.create_test_user(template_id)
        if not human_user_id:
            return False
        
        print("\n" + "🚀" + "="*58 + "🚀")
        print("开始执行评论生成逻辑测试...")
        print("🚀" + "="*58 + "🚀")
        
        # 6. 测试各个组件
        try:
            # 测试帖子统计预测
            stats = self.test_post_stats_prediction(template_id, post_content)
            
            # 测试种子评论生成
            seeds = self.test_lv1_seeds_generation(template_id, post_content)
            
            # 测试评论扩展
            if seeds:
                self.test_comment_expansion(template_id, post_content, seeds)
            
            # 测试点赞数预测
            self.test_comment_likes_prediction(template_id)
            
            # 测试完整帖子服务
            self.test_post_service(template_id, post_content, human_user_id)
            
            print("\n" + "🎉" + "="*58 + "🎉")
            print("所有测试完成！")
            print("🎉" + "="*58 + "🎉")
            
            return True
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            print(f"❌ 测试过程中发生错误: {e}")
            return False
    
    def cleanup(self):
        """清理测试数据"""
        try:
            if self.current_human_user:
                # 这里可以添加清理逻辑，比如删除测试用户
                print(f"🧹 清理测试用户: {self.current_human_user.username}")
            if self.db:
                self.db.close()
        except Exception as e:
            logger.error(f"清理失败: {e}")


def main():
    """主函数"""
    # 测试配置 - 在这里修改测试参数
    TEST_CONFIG = {
        "template_id": 1,  # 指定模板ID，None表示使用第一个可用模板
        "post_content": "今天天气真好，心情也很棒！"  # 测试用的帖子内容
    }
    
    tester = CommentGenerationTester(
        template_id=TEST_CONFIG["template_id"],
        post_content=TEST_CONFIG["post_content"]
    )
    
    try:
        success = tester.run_full_test()
        if success:
            print("\n✅ 测试成功完成！")
        else:
            print("\n❌ 测试失败或中断")
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"\n❌ 测试运行失败: {e}")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()

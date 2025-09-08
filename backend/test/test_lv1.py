#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI LV1评论生成测试脚本 - 本地变量版本

使用方法：
1. 确保已配置好API密钥
2. 运行脚本：python test_lv1.py
3. 观察评论生成过程和结果

功能：
- 测试所有评论生成相关的方法
- 使用本地变量模拟数据，不涉及数据库
- 支持自定义帖子内容
- 显示详细的生成过程和统计信息
"""

import json
import os
import sys
import time
from typing import Dict, Optional, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_module.post_related import predict_post_stats
from backend.ai_module.comment_related import (
    generate_lv1_seeds,
    expand_lv1_comments,
    predict_comment_likes
)
from backend.models import Attitude
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CommentGenerationTester:
    """评论生成测试器 - 本地变量版本"""
    
    def __init__(self, template_id=None, post_content=None):
        # 本地测试数据 - 用户模板
        self.user_template = {
            "template_id": 1,
            "template_name": "STAR",
            "persona": "这是一个在社交媒体上极具人气的娱乐明星角色：她是一位活跃在多个领域的全能型明星，涵盖音乐、影视、时尚等行业，拥有百万级粉丝，深受年轻群体喜爱。她的公众形象具有鲜明的风格——偏酷、前卫且带有中性气质，这种风格体现在她的日常穿搭、妆容、发型以及社交媒体内容中。她偏好街头风、工装或极简剪裁，常以冷静、自信的形象出镜，展现出不拘一格的魅力。她在社交平台上非常活跃，常常分享自己的生活碎片、幕后花絮、旅行日记、以及新歌、电影或代言项目的预告。她的内容既真实又带有高度审美感，融合了艺术性与潮流感，给粉丝一种既遥远又贴近的双重印象。她偶尔会出现在自己帖子的评论区，亲自回复部分粉丝的留言，这种互动让她的粉丝们异常活跃，常常绞尽脑汁写出风趣、有创意或充满情感的评论，希望能引起偶像的注意。她本人虽然神秘低调，但在互动中却展现出幽默和细腻的一面，进一步加深了她的影响力与亲和力。请基于上述设定生成与她相关的内容或对话风格。",
            "follower_count": 100,
            "commenter_distribution": {
                "极差": 0.03,
                "不友善": 0.11,
                "中立": 0.25,
                "友善": 0.31,
                "极好": 0.23,
                "狂热": 0.07
            }
        }
        
        # 测试配置 - 可以通过参数或直接修改这些变量
        self.template_id = template_id or 1
        self.post_content = post_content or "今天天气真好，心情也很棒！"
        
        # 用于收集所有生成的LV1评论
        self.all_lv1_comments = {
            "seeds": {},  # 种子评论
            "expanded": {},  # 扩展评论
            "metadata": {
                "template_id": None,
                "template_name": None,
                "post_content": None,
                "generation_time": None,
                "total_seeds": 0,
                "total_expanded": 0
            }
        }
        
    def load_user_templates(self):
        """加载用户模板 - 本地版本"""
        try:
            logger.info(f"使用本地用户模板: {self.user_template['template_name']}")
            return True
        except Exception as e:
            logger.error(f"加载用户模板失败: {e}")
            return False
    
    def display_templates(self):
        """显示可用的用户模板"""
        print("\n" + "="*60)
        print(" 可用的用户模板:")
        print("="*60)
        
        print(f"1. {self.user_template['template_name']}")
        print(f"    人设: {self.user_template['persona'][:100]}...")
        print(f"    粉丝数: {self.user_template['follower_count']}")
        print(f"   - 评论者分布: {json.dumps(self.user_template['commenter_distribution'], ensure_ascii=False, indent=6)}")
        print("-" * 60)
    
    def select_template(self) -> Optional[int]:
        """选择用户模板"""
        print(f"使用本地模板: {self.user_template['template_name']}")
        return self.user_template['template_id']
    
    def get_post_content(self) -> Optional[str]:
        """获取帖子内容"""
        print("\n" + "="*60)
        print(" 帖子内容:")
        print("="*60)
        
        if not self.post_content:
            print(" 帖子内容不能为空")
            return None
            
        if len(self.post_content) > 140:
            print(" 帖子内容不能超过140个字符")
            return None
            
        print(f" 帖子内容: {self.post_content}")
        return self.post_content
    
    def create_test_user(self, template_id: int) -> Optional[int]:
        """创建测试用户 - 本地版本"""
        try:
            # 生成唯一的用户名
            import time
            username = f"测试用户_{int(time.time())}"
            
            # 模拟人类用户对象
            human_user = {
                "user_id": 999999,  # 模拟用户ID
                "username": username,
                "user_template_id": template_id,
                "avatar_path": ""
            }
            
            print(f" 创建测试用户: {username} (ID: {human_user['user_id']})")
            self.current_human_user = human_user
            return human_user['user_id']
            
        except Exception as e:
            logger.error(f"创建测试用户失败: {e}")
            print(f" 创建测试用户失败: {e}")
            return None
    
    def test_post_stats_prediction(self, template_id: int, post_content: str):
        """测试帖子统计数据预测"""
        print("\n" + "="*60)
        print(" 测试帖子统计数据预测")
        print("="*60)
        
        try:
            # 使用本地模板数据
            template = self.user_template
            
            # 模拟历史帖子
            history_posts = [
                "昨天的工作很充实！",
                "新项目进展顺利",
                "感谢大家的支持"
            ]
            
            print(f" 预测参数:")
            print(f"   人设: {template['persona'][:50]}...")
            print(f"   粉丝数: {template['follower_count']}")
            print(f"   帖子内容: {post_content}")
            print(f"   历史帖子: {history_posts}")
            
            # 调用预测方法
            stats = predict_post_stats(
                persona=template['persona'],
                follower_count=template['follower_count'],
                post_content=post_content,
                history_posts=history_posts,
                retry=3
            )
            
            print(f"\n 预测结果:")
            print(f"   新增粉丝数: {stats['pred_new_follower_count']}")
            print(f"   评论总数: {stats['pred_comment_count']}")
            print(f"   点赞总数: {stats['pred_like_count']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"帖子统计预测失败: {e}")
            print(f" 帖子统计预测失败: {e}")
            return None
    
    def test_lv1_seeds_generation(self, template_id: int, post_content: str):
        """测试一级种子评论生成"""
        print("\n" + "="*60)
        print(" 测试一级种子评论生成")
        print("="*60)
        
        try:
            # 使用本地模板数据
            template = self.user_template
            
            # 模拟历史帖子
            history_posts = [
                "昨天的工作很充实！",
                "新项目进展顺利",
                "感谢大家的支持"
            ]
            
            print(f" 生成参数:")
            print(f"   人设: {template['persona'][:50]}...")
            print(f"   帖子内容: {post_content}")
            
            # 调用种子评论生成方法
            seeds = generate_lv1_seeds(
                persona=template['persona'],
                post_content=post_content,
                history_posts=history_posts,
                retry=3
            )
            
            print(f"\n 种子评论生成结果:")
            total_seeds = 0
            for attitude, comments in seeds.items():
                print(f"\n   {attitude.value} ({len(comments)}条):")
                # 收集种子评论数据
                if attitude.value not in self.all_lv1_comments["seeds"]:
                    self.all_lv1_comments["seeds"][attitude.value] = []
                for i, comment in enumerate(comments, 1):
                    print(f"     {i}. {comment}")
                    self.all_lv1_comments["seeds"][attitude.value].append({
                        "index": i,
                        "content": comment,
                        "type": "seed"
                    })
                    total_seeds += 1
            
            print(f"\n 总计生成 {total_seeds} 条种子评论")
            return seeds
            
        except Exception as e:
            logger.error(f"种子评论生成失败: {e}")
            print(f" 种子评论生成失败: {e}")
            return None
    
    def test_comment_expansion(self, template_id: int, post_content: str, seeds: Dict):
        """测试评论扩展"""
        print("\n" + "="*60)
        print(" 测试评论扩展")
        print("="*60)
        
        try:
            # 使用本地模板数据
            template = self.user_template
            
            total_expanded = 0
            
            for attitude, comments in seeds.items():
                if not comments:
                    continue
                    
                print(f"\n 扩展 {attitude.value} 态度评论:")
                print(f"   原始种子评论 ({len(comments)}条):")
                for i, seed_comment in enumerate(comments, 1):
                    print(f"     种子{i}: {seed_comment}")
                
                # 初始化扩展评论收集
                if attitude.value not in self.all_lv1_comments["expanded"]:
                    self.all_lv1_comments["expanded"][attitude.value] = []
                
                # 为每个种子评论生成扩展
                all_expanded_for_attitude = []
                for i, seed_comment in enumerate(comments, 1):
                    print(f"\n     基于种子{i}的扩展:")
                    expanded = expand_lv1_comments(
                        persona=template['persona'],
                        post_content=post_content,
                        attitude_type=attitude,
                        seed_comments=[seed_comment],
                        expand_count=3,
                        retry=3
                    )
                    
                    print(f"       扩展结果 ({len(expanded)}条):")
                    for j, comment in enumerate(expanded, 1):
                        print(f"         {j}. {comment}")
                        all_expanded_for_attitude.append(comment)
                        # 收集扩展评论数据
                        self.all_lv1_comments["expanded"][attitude.value].append({
                            "index": len(self.all_lv1_comments["expanded"][attitude.value]) + 1,
                            "content": comment,
                            "type": "expanded",
                            "parent_seed": seed_comment,
                            "parent_seed_index": i
                        })
                        total_expanded += 1
                
                print(f"\n   {attitude.value} 态度总计扩展: {len(all_expanded_for_attitude)} 条评论")
            
            print(f"\n 总计扩展 {total_expanded} 条评论")
            return True
            
        except Exception as e:
            logger.error(f"评论扩展失败: {e}")
            print(f" 评论扩展失败: {e}")
            return False
    
    def save_comments_to_json(self, template_id: int):
        """保存所有LV1评论到JSON文件"""
        try:
            # 更新元数据
            template = self.user_template
            self.all_lv1_comments["metadata"]["template_id"] = template_id
            self.all_lv1_comments["metadata"]["template_name"] = template["template_name"]
            self.all_lv1_comments["metadata"]["post_content"] = self.post_content
            self.all_lv1_comments["metadata"]["generation_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 计算总数
            total_seeds = sum(len(comments) for comments in self.all_lv1_comments["seeds"].values())
            total_expanded = sum(len(comments) for comments in self.all_lv1_comments["expanded"].values())
            self.all_lv1_comments["metadata"]["total_seeds"] = total_seeds
            self.all_lv1_comments["metadata"]["total_expanded"] = total_expanded
            
            # 调试信息
            print(f"\n 调试信息:")
            print(f"   种子评论数据结构: {list(self.all_lv1_comments['seeds'].keys())}")
            print(f"   扩展评论数据结构: {list(self.all_lv1_comments['expanded'].keys())}")
            print(f"   种子评论总数: {total_seeds}")
            print(f"   扩展评论总数: {total_expanded}")
            
            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"lv1_comments_{template['template_name']}_{timestamp}.json"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            # 保存到JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.all_lv1_comments, f, ensure_ascii=False, indent=2)
            
            print(f"\n" + "="*60)
            print(" LV1评论数据保存")
            print("="*60)
            print(f" 保存文件: {filename}")
            print(f" 文件路径: {filepath}")
            print(f" 种子评论: {total_seeds} 条")
            print(f" 扩展评论: {total_expanded} 条")
            print(f" 总计评论: {total_seeds + total_expanded} 条")
            print(f" 模板名称: {template['template_name']}")
            print(f" 生成时间: {self.all_lv1_comments['metadata']['generation_time']}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"保存评论数据失败: {e}")
            print(f" 保存评论数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_comment_likes_prediction(self, template_id: int):
        """测试评论点赞数预测"""
        print("\n" + "="*60)
        print(" 测试评论点赞数预测")
        print("="*60)
        
        try:
            # 使用本地模板数据
            template = self.user_template
            
            print(f" 预测参数:")
            print(f"   粉丝数: {template['follower_count']}")
            print(f"   浮动范围: 0.9")
            print(f"   缩放指数: 0.01")
            
            # 生成多个预测结果
            predictions = []
            for i in range(5):
                likes = predict_comment_likes(
                    follower_count=template['follower_count'],
                    float_range=0.9,
                    zoom_index=0.01
                )
                predictions.append(likes)
            
            print(f"\n 点赞数预测结果:")
            for i, likes in enumerate(predictions, 1):
                print(f"   预测 {i}: {likes} 个赞")
            
            avg_likes = sum(predictions) / len(predictions)
            print(f"\n 平均点赞数: {avg_likes:.1f}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"点赞数预测失败: {e}")
            print(f" 点赞数预测失败: {e}")
            return None
    
    def test_post_service(self, template_id: int, post_content: str, human_user_id: int):
        """测试完整的帖子服务 - 本地版本（跳过数据库相关测试）"""
        print("\n" + "="*60)
        print(" 测试完整的帖子服务")
        print("="*60)
        
        try:
            print(f" 服务参数:")
            print(f"   模板ID: {template_id}")
            print(f"   帖子内容: {post_content}")
            print(f"   人类用户ID: {human_user_id}")
            
            print(f"\n 注意: 帖子服务需要数据库连接，本地测试版本跳过此测试")
            print(f" 如需测试完整帖子服务，请使用数据库版本")
            
            return True
            
        except Exception as e:
            logger.error(f"帖子服务测试失败: {e}")
            print(f" 帖子服务测试失败: {e}")
            return None
    
    def run_full_test(self):
        """运行完整测试"""
        print(" InfluAI 评论生成逻辑测试")
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
        
        print("\n" + "" + "="*58 + "")
        print("开始执行评论生成逻辑测试...")
        print("" + "="*58 + "")
        
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
            
            # 保存所有LV1评论到JSON文件
            self.save_comments_to_json(template_id)
            
            print("\n" + "" + "="*58 + "")
            print("所有测试完成！")
            print("" + "="*58 + "")
            
            return True
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            print(f" 测试过程中发生错误: {e}")
            return False
    
    def cleanup(self):
        """清理测试数据 - 本地版本"""
        try:
            if self.current_human_user:
                # 本地版本不需要清理数据库
                print(f"清理测试用户: {self.current_human_user['username']}")
        except Exception as e:
            logger.error(f"清理失败: {e}")


def main():
    """主函数 - 本地版本"""
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
            print("\n 测试成功完成！")
        else:
            print("\n 测试失败或中断")
    except KeyboardInterrupt:
        print("\n 测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"\n 测试运行失败: {e}")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()

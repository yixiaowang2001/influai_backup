#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帖子统计数据预测测试脚本
测试基于人设和帖子内容生成相关数据指标的功能
"""

import json
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_module.post_related import predict_post_stats
from backend.ai_module.prompts import get_predict_post_stats_prompt

# 本地人设模板数据
LOCAL_PERSONA_TEMPLATES = {
    "STAR": {
        "template_id": 1,
        "template_name": "STAR",
        "persona": "这是一个在社交媒体上极具人气的娱乐明星角色：她是一位活跃在多个领域的全能型明星，涵盖音乐、影视、时尚等行业，拥有百万级粉丝，深受年轻群体喜爱。她的公众形象具有鲜明的风格——偏酷、前卫且带有中性气质，这种风格体现在她的日常穿搭、妆容、发型以及社交媒体内容中。她偏好街头风、工装或极简剪裁，常以冷静、自信的形象出镜，展现出不拘一格的魅力。她在社交平台上非常活跃，常常分享自己的生活碎片、幕后花絮、旅行日记、以及新歌、电影或代言项目的预告。她的内容既真实又带有高度审美感，融合了艺术性与潮流感，给粉丝一种既遥远又贴近的双重印象。她偶尔会出现在自己帖子的评论区，亲自回复部分粉丝的留言，这种互动让她的粉丝们异常活跃，常常绞尽脑汁写出风趣、有创意或充满情感的评论，希望能引起偶像的注意。她本人虽然神秘低调，但在互动中却展现出幽默和细腻的一面，进一步加深了她的影响力与亲和力。请基于上述设定生成与她相关的内容或对话风格。",
        "follower_count": 10000,
        "commenter_distribution": {
            "极差": 0.03,
            "不友善": 0.11,
            "中立": 0.25,
            "友善": 0.31,
            "极好": 0.23,
            "狂热": 0.07
        }
    },
    "BEAUTY": {
        "template_id": 2,
        "template_name": "BEAUTY",
        "persona": "专业美妆博主，专注于美妆护肤内容分享。她拥有丰富的化妆技巧和护肤知识，经常分享实用的美妆教程、产品评测和护肤心得。她的内容专业且实用，深受年轻女性粉丝喜爱。她善于发现和推荐性价比高的美妆产品，经常与粉丝分享购物心得和使用技巧。她的风格偏向清新自然，偶尔也会尝试大胆的妆容造型。",
        "follower_count": 5000,
        "commenter_distribution": {
            "极差": 0.02,
            "不友善": 0.08,
            "中立": 0.20,
            "友善": 0.35,
            "极好": 0.28,
            "狂热": 0.07
        }
    },
    "FITNESS": {
        "template_id": 3,
        "template_name": "FITNESS",
        "persona": "专业健身教练和健康生活方式倡导者。她拥有多年的健身经验，经常分享科学的健身方法、营养搭配和健康生活理念。她的内容积极向上，充满正能量，激励粉丝坚持运动和健康生活。她善于制定个性化的健身计划，经常分享自己的健身成果和心得体会。",
        "follower_count": 80,
        "commenter_distribution": {
            "极差": 0.01,
            "不友善": 0.05,
            "中立": 0.18,
            "友善": 0.40,
            "极好": 0.30,
            "狂热": 0.06
        }
    },
    "TECH": {
        "template_id": 4,
        "template_name": "TECH",
        "persona": "资深科技媒体人和产品评测专家。他对科技产品有深入的了解和独到的见解，经常分享最新的科技资讯、产品评测和技术分析。他的内容专业且客观，深受科技爱好者和数码产品用户喜爱。他善于发现产品的优缺点，为消费者提供有价值的购买建议。",
        "follower_count": 150,
        "commenter_distribution": {
            "极差": 0.05,
            "不友善": 0.15,
            "中立": 0.35,
            "友善": 0.30,
            "极好": 0.12,
            "狂热": 0.03
        }
    },
    "LIFESTYLE": {
        "template_id": 5,
        "template_name": "LIFESTYLE",
        "persona": "热爱生活的博主，专注于分享日常生活和生活方式。她的内容贴近生活，充满温暖和正能量。她善于发现生活中的美好，经常分享美食、旅行、家居装饰等生活相关内容。她的风格温馨自然，给粉丝带来舒适和愉悦的感受。",
        "follower_count": 300000,
        "commenter_distribution": {
            "极差": 0.01,
            "不友善": 0.04,
            "中立": 0.15,
            "友善": 0.45,
            "极好": 0.30,
            "狂热": 0.05
        }
    },
    "FOOD": {
        "template_id": 6,
        "template_name": "FOOD",
        "persona": "专业美食博主和烹饪达人。她热爱美食，经常分享各种美食制作方法、探店体验和食材介绍。她的内容色香味俱全，深受美食爱好者喜爱。她善于发现和推荐各种美食，经常与粉丝分享烹饪心得和美食文化。",
        "follower_count": 6000,
        "commenter_distribution": {
            "极差": 0.01,
            "不友善": 0.03,
            "中立": 0.12,
            "友善": 0.42,
            "极好": 0.35,
            "狂热": 0.07
        }
    }
}


class StatsPredictionTester:
    """帖子统计数据预测测试器"""

    def __init__(self):
        self.test_results = []

    def show_local_templates(self):
        """显示本地人设模板信息"""
        print("\n=== 本地人设模板信息 ===")
        for name, template in LOCAL_PERSONA_TEMPLATES.items():
            print(f"\n{template['template_name']} ({name}):")
            print(f"  模板ID: {template['template_id']}")
            print(f"  粉丝数: {template['follower_count']:,}")
            print(f"  人设描述: {template['persona'][:100]}...")
            print(f"  评论者分布:")
            for attitude, ratio in template['commenter_distribution'].items():
                print(f"    {attitude}: {ratio:.1%}")

    def test_predict_post_stats(self, persona, follower_count, post_content, history_posts=None):
        """测试帖子统计数据预测功能"""
        print(f"\n=== 测试帖子统计数据预测 ===")
        print(f"人设: {persona}")
        print(f"粉丝数: {follower_count}")
        print(f"帖子内容: {post_content}")
        if history_posts:
            print(f"历史帖子: {history_posts}")

        try:
            # 调用预测函数
            result = predict_post_stats(persona, follower_count, post_content, history_posts)

            print(f"\n预测结果:")
            print(f"新增关注: {result.get('pred_new_follower_count', 'N/A')}")
            print(f"评论量: {result.get('pred_comment_count', 'N/A')}")
            print(f"点赞量: {result.get('pred_like_count', 'N/A')}")

            # 保存测试结果
            test_result = {
                'timestamp': datetime.now().isoformat(),
                'persona': persona,
                'follower_count': follower_count,
                'post_content': post_content,
                'history_posts': history_posts,
                'prediction': result
            }
            self.test_results.append(test_result)

            return result

        except Exception as e:
            print(f"预测失败: {str(e)}")
            return None

    def test_prompt_generation(self, persona, follower_count, post_content, history_posts=None):
        """测试prompt生成功能"""
        print(f"\n=== 测试Prompt生成 ===")

        try:
            system_prompt, user_prompt = get_predict_post_stats_prompt(
                persona, follower_count, post_content, history_posts
            )

            print(f"\n系统Prompt:")
            print(system_prompt)
            print(f"\n用户Prompt:")
            print(user_prompt)

            return system_prompt, user_prompt

        except Exception as e:
            print(f"Prompt生成失败: {str(e)}")
            return None, None

    def run_comprehensive_test(self):
        """运行综合测试"""
        print("开始帖子统计数据预测综合测试...")
        print(f"使用本地人设模板: {list(LOCAL_PERSONA_TEMPLATES.keys())}")

        # 测试用例1: STAR明星
        print("\n" + "=" * 50)
        print("测试用例1: STAR明星")
        template = LOCAL_PERSONA_TEMPLATES["STAR"]
        self.test_predict_post_stats(
            persona=template["persona"],
            follower_count=template["follower_count"],
            post_content="新电影即将上映，希望大家多多支持！这次的角色很有挑战性，期待与大家分享更多幕后故事",
            history_posts=["宣传了新专辑", "分享了拍摄花絮", "时尚穿搭分享"]
        )

        # 测试用例2: 美妆博主
        print("\n" + "=" * 50)
        print("测试用例2: 美妆博主")
        template = LOCAL_PERSONA_TEMPLATES["BEAUTY"]
        self.test_predict_post_stats(
            persona=template["persona"],
            follower_count=template["follower_count"],
            post_content="今天试了新买的口红，颜色超级好看！大家觉得怎么样？",
            history_posts=["昨天分享了护肤心得", "前天推荐了面膜", "妆容教程分享"]
        )

        # 测试用例3: 健身达人
        print("\n" + "=" * 50)
        print("测试用例3: 健身达人")
        template = LOCAL_PERSONA_TEMPLATES["FITNESS"]
        self.test_predict_post_stats(
            persona=template["persona"],
            follower_count=template["follower_count"],
            post_content="坚持健身3个月了，体重减了15斤！感谢大家的鼓励和支持",
            history_posts=["分享了健身计划", "推荐了健身器材", "健康饮食建议"]
        )

        # 测试用例4: 科技博主
        print("\n" + "=" * 50)
        print("测试用例4: 科技博主")
        template = LOCAL_PERSONA_TEMPLATES["TECH"]
        self.test_predict_post_stats(
            persona=template["persona"],
            follower_count=template["follower_count"],
            post_content="我觉得现在的手机价格太贵了，性价比越来越低，大家怎么看？",
            history_posts=["评测了新手机", "分析了市场趋势", "技术解析分享"]
        )

        # 测试用例5: 生活博主
        print("\n" + "=" * 50)
        print("测试用例5: 生活博主")
        template = LOCAL_PERSONA_TEMPLATES["LIFESTYLE"]
        self.test_predict_post_stats(
            persona=template["persona"],
            follower_count=template["follower_count"],
            post_content="今天天气真好，在公园里散步，心情特别舒畅",
            history_posts=["分享了美食", "推荐了旅游景点", "家居装饰心得"]
        )

        # 测试用例6: 美食博主
        print("\n" + "=" * 50)
        print("测试用例6: 美食博主")
        template = LOCAL_PERSONA_TEMPLATES["FOOD"]
        self.test_predict_post_stats(
            persona=template["persona"],
            follower_count=template["follower_count"],
            post_content="今天做了红烧肉，肥而不腻，入口即化！有想学的吗？",
            history_posts=["分享了糖醋排骨", "推荐了厨房用品", "食材选购技巧"]
        )

    def save_test_results(self, filename=None):
        """保存测试结果到JSON文件"""
        if not filename:
            filename = "stats_test_results.json"

        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n测试结果已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存测试结果失败: {str(e)}")
            return None

    def analyze_results(self):
        """分析测试结果"""
        if not self.test_results:
            print("没有测试结果可分析")
            return

        print(f"\n=== 测试结果分析 ===")
        print(f"总测试用例数: {len(self.test_results)}")

        # 分析粉丝数与评论量的关系
        print(f"\n粉丝数与评论量关系分析:")
        for result in self.test_results:
            follower_count = result['follower_count']
            comment_count = result['prediction'].get('pred_comment_count', 0)
            print(f"粉丝数: {follower_count:,} -> 评论量: {comment_count}")

        # 分析不同人设的表现
        print(f"\n不同人设表现分析:")
        personas = {}
        for result in self.test_results:
            persona = result['persona']
            if persona not in personas:
                personas[persona] = []
            personas[persona].append(result['prediction'].get('pred_comment_count', 0))

        for persona, comment_counts in personas.items():
            avg_comments = sum(comment_counts) / len(comment_counts)
            print(f"{persona}: 平均评论量 {avg_comments:.1f}")


def main():
    """主函数"""
    print("帖子统计数据预测测试工具")
    print("=" * 50)

    tester = StatsPredictionTester()

    try:
        # 显示本地模板信息
        tester.show_local_templates()

        # 运行综合测试
        tester.run_comprehensive_test()

        # 分析结果
        tester.analyze_results()

        # 保存结果
        tester.save_test_results()

        print(f"\n测试完成！")

    except KeyboardInterrupt:
        print(f"\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main()

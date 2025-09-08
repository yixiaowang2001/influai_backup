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
import random
import sys
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_module.comment_related import generate_lvn_comments
from backend.models import Attitude
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LVNCommentTester:
    """LVN评论生成测试器 - 深度优先自我问答方案"""

    def __init__(self):
        # 测试数据 - 用户模板
        self.user_template = {
            "template_id": 1,
            "template_name": "STAR",
            "persona": "这是一个刚刚注册社交媒体账号的、极具人气的娱乐明星角色：她是一位活跃在多个领域的全能型明星，涵盖音乐、影视、时尚等行业，深受年轻群体喜爱。她的公众形象具有鲜明的风格——偏酷、前卫且带有中性气质，这种风格体现在她的日常穿搭、妆容、发型以及社交媒体内容中。她偏好街头风、工装或极简剪裁，常以冷静、自信的形象出镜，展现出不拘一格的魅力。她在社交平台上非常活跃，常常分享自己的生活碎片、幕后花絮、旅行日记、以及新歌、电影或代言项目的预告。她的内容既真实又带有高度审美感，融合了艺术性与潮流感，给粉丝一种既遥远又贴近的双重印象。她偶尔会出现在自己帖子的评论区，亲自回复部分粉丝的留言，这种互动让她的粉丝们异常活跃，常常绞尽脑汁写出风趣、有创意或充满情感的评论，希望能引起偶像的注意。她本人虽然神秘低调，但在互动中却展现出幽默和细腻的一面，进一步加深了她的影响力与亲和力。请基于上述设定生成与她相关的内容或对话风格。",
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

        # 测试数据 - 帖子内容
        self.post_content = "今天好累，不想演出……"

        # 测试数据 - LV1评论
        self.lv1_comments = {
            Attitude.PERFECT: [
                "累就别硬撑啦呀，期待满血回归！",
                "休息一下也不要紧嘛，照顾好自己最重要～",
                "身体最重要啦！等你好精神再闪耀舞台哦",
                "天啊，看到你这样我也心疼得不行！谁要是说你不勤奋，我第一个不服气哈哈哈。",
                "我的 goddess 啊，累的话就休息吧！那些质疑你努力的人纯粹眼瞎，我来帮你说理去。",
                " OMG，你也太真实了吧！累就说累嘛，咱不逞强。有人胆敢抹黑你努力的程度，找我理论去啦！",
                "自从你发布新项目预告后，我一直默默为你加油。每个人都能看到你的努力和用心，要是累了就别硬撑，我们都会等你满血归来。",
                "小姐姐，你有多拼命我们粉丝比谁都清楚！休息一下并不是退缩，而是为了下一次更好的回归呀。无论如何，这里有群死忠粉永远支持着你！",
                "从你开始透露新项目计划到现在，每一天都充满期待。但比起完美的作品，你的健康更重要！累了就停下来歇歇吧，我们会像从前一样一直守候着。"
            ],
            Attitude.BAD: [
                "哎呀，累就不累呗，装什么神秘兮兮？",
                "哼，天好累？这可不是咱 conocer 的作风吧！?",
                "少来这套啦，谁不知道你其实精力无限呢～",
                "不想上就休息嘛，Fans又不会因为你一次暂停就跑了。",
                "累就该好好调整，没人会强迫你一直演出吧。",
                "状态不好就不强求呗，生活比工作更重要呀。",
                "前天不是还在台上跳到飞起吗？今天就这么颓了？明星也有职业底线吧！",
                "昨天还不是干劲十足？怎么转眼就摆烂了呢？粉丝都指望你加油呢！",
                "刚刚还在宣传新戏多辛苦，现在就想划水？艺人也该有点责任心呀！"
            ],
            Attitude.NEUTRAL: [
                "适当放松一下也没啥问题呀～毕竟健康最重要！?",
                "不想演出就休息呗，照顾好自己才是正经事～🤔",
                "累了就暂停一下嘛，观众也会理解的啦～🫥",
                "大家都一样会有疲倦的时候，但你可不能放弃哦，继续冲！",
                "工作量这么大，感觉累是正常的啦。不过咱们还得调整状态往前走呀！",
                "就算有再大的压力和疲惫，也请咬咬牙坚持一下，我们都期待着你的表现呢！",
                "这让我想到自己刚开始拍戏时，总抱怨累，不过后来学会调节自己，状态就变好啦%",
                "想起当年第一次录歌的时候，也是觉得特别辛苦，但适应之后就好了呢。",
                "刚出道时我也常常喊累，但是随着时间慢慢摸索出方法，感觉就没那么累了。"
            ],
            Attitude.NEUTRAL_POSITIVE: [
                "小姐姐打起精神来，你最强啦！",
                "坚持一下下就好咯，我们都爱你呦～",
                "别泄气呀，累了歇歇再战，期待更棒的你呢！",
                "忙累了就别硬撑，你一直都在超水准发挥呢！粉丝们都等着你恢复精力后的新行程~",
                "确实需要休息，保持最佳状态才能带来更好作品啊！期待你调整好后再告诉我们计划哦。",
                "歇一歇没关系，完美演出源于充分准备和休息！下次行程啥时候定呀，我们都超期待！",
                "看到你这样子也感觉超真实呢！明星也会有压力和疲惫，要好好爱惜自己呀～希望你早日元气满满哦！",
                "原来偶像背后也有很多不容易啊！好好休息调整心态，你的粉丝们永远都会支持你的啦～",
                "忙碌的日子总会让人身心俱疲，但别忘了照顾好自己哦！期待更棒的你出现在我们面前，加油！"
            ],
            Attitude.NEUTRAL_NEGATIVE: [
                "撑不住就歇会儿，谁求你出来博眼球?",
                "疲惫就干脆别勉强，没人稀罕看你硬撑!",
                "状态不好就回家躺平呗，出来装什么强?",
                "摆烂呢？可别又在这儿糊弄我们这些真情实感的粉丝哦。",
                "又是这套疲惫说辞？感觉就是在故意炒作吧，真够可以的。",
                "累了就可以随便应付了？看来玩转粉丝情绪是你最擅长的事儿呢。",
                "前一秒还说热爱舞台，后一秒就说累不想演，态度转变也太快了吧🤔",
                "这情绪波动未免也太大了点吧？昨天还好好的，今天就不想工作了？",
                "累了可以休息，但不要因为短暂的疲惫就逃避责任哦，这样的职业态度有点让人失望🤔"
            ],
            Attitude.GOOD: [
                "女神是真的累了呢！歇一歇才更有精神征服舞台呀！",
                "天天这么拼，辛苦是肯定的，但是我们的女神永远是最棒的！",
                "努力的工作让妳更加耀眼，不过也别忘了照顾自己哦～",
                "再累也别停下脚步啊，你永远是我们追逐梦想的榜样！",
                "疲惫只是暂时的，继续加油！你是我们的无限动力源泉！",
                "虽然累了但要相信自己的实力，你的光芒一直都在引领着我们！",
                "哪怕累成这样，你也依然是我心中无敌耀眼的 superstar，下次演出肯定会更炸！✨加油啊!",
                "劳累是暂时的，你的闪耀可是永久的，期待你再次征服舞台的瞬间，加油女神！🌟",
                "累了就休息，但在我眼里你永远是最亮的那颗星，下一次表演绝对更出彩！🔥冲鸭！"
            ],
        }

        # 态度权重映射
        self.attitude_weights = {
            Attitude.PERFECT: 0.95,  # 狂热态度
            Attitude.BAD: 0.9,  # 极差态度
            Attitude.GOOD: 0.7,  # 极好态度
            Attitude.NEUTRAL_NEGATIVE: 0.6,  # 不友善态度
            Attitude.NEUTRAL_POSITIVE: 0.4,  # 友善态度
            Attitude.NEUTRAL: 0.0  # 中立态度
        }

    def calculate_heat_score(self, comment: str, attitude: Attitude) -> float:
        """
        计算评论的热度分数
        
        Args:
            comment: 评论内容
            attitude: 态度类型
            
        Returns:
            float: 热度分数
        """
        # 态度强度因子
        attitude_factor = self.attitude_weights.get(attitude, 0.0)

        # 评论长度因子 (0-1)
        length_factor = min(len(comment) / 50, 1.0)

        # 表情符号因子
        emoji_count = sum(1 for char in comment if
                          ord(char) > 127 and char in "😀😁😂🤣😃😄😅😆😉😊😋😎😍😘🥰😗😙😚☺️🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹️🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵😡😠🤬😷🤒🤕🤢🤮🤧😇🤠🤡🥳🥴🥺🤥🤫🤭🧐🤓😈👿👹👺💀☠️👻👽👾🤖💩😺😸😹😻😼😽🙀😿😾")
        emoji_factor = min(emoji_count * 0.5, 1.0)

        # 网络用语因子
        internet_words = ["卧槽", "牛逼", "绝了", "yyds", "绝绝子", "yyds", "666", "绝了", "太棒了", "爱了", "绝了",
                          "yyds"]
        internet_factor = sum(1 for word in internet_words if word in comment) * 0.3
        internet_factor = min(internet_factor, 1.0)

        # 计算总热度分数
        heat_score = attitude_factor + length_factor + emoji_factor + internet_factor

        return heat_score

    def select_hot_comments(self, max_hot: int = 10, max_regular: int = 20) -> Tuple[
        List[Tuple[str, Attitude, float]], List[Tuple[str, Attitude, float]]]:
        """
        选择热门评论和普通评论
        
        Args:
            max_hot: 最大热门评论数量
            max_regular: 最大普通评论数量
            
        Returns:
            Tuple[List[Tuple[str, Attitude, float]], List[Tuple[str, Attitude, float]]]: (热门评论, 普通评论)
        """
        print("\n" + "=" * 60)
        print(" 热度分数计算和评论筛选")
        print("=" * 60)

        # 计算所有评论的热度分数
        all_comments_with_scores = []
        for attitude, comments in self.lv1_comments.items():
            for comment in comments:
                heat_score = self.calculate_heat_score(comment, attitude)
                all_comments_with_scores.append((comment, attitude, heat_score))

        # 按热度分数排序
        all_comments_with_scores.sort(key=lambda x: x[2], reverse=True)

        print(" 热度分数计算结果:")
        for i, (comment, attitude, score) in enumerate(all_comments_with_scores, 1):
            print(f"   {i:2d}. [{attitude.value:8s}] {comment[:30]:30s} (热度: {score:.2f})")

        # 选择热门评论和普通评论
        hot_comments = all_comments_with_scores[:max_hot]
        regular_comments = all_comments_with_scores[max_hot:max_hot + max_regular]

        print(f"\n 热门评论选择 ({len(hot_comments)}条):")
        for i, (comment, attitude, score) in enumerate(hot_comments, 1):
            print(f"   {i:2d}. [{attitude.value:8s}] {comment[:40]:40s} (热度: {score:.2f})")

        print(f"\n 普通评论选择 ({len(regular_comments)}条):")
        for i, (comment, attitude, score) in enumerate(regular_comments, 1):
            print(f"   {i:2d}. [{attitude.value:8s}] {comment[:40]:40s} (热度: {score:.2f})")

        return hot_comments, regular_comments

    def generate_dialogue_chain(self, parent_comment: str, parent_attitude: Attitude, max_depth: int = 4) -> List[Dict]:
        """
        生成对话链
        
        Args:
            parent_comment: 父评论
            parent_attitude: 父评论态度
            max_depth: 最大深度
            
        Returns:
            List[Dict]: 对话链
        """
        print(f"\n  生成对话链 - 父评论: {parent_comment[:30]}...")
        print(f"  父评论态度: {parent_attitude.value}")
        print(f"  最大深度: {max_depth}")

        dialogue_chain = []
        current_comment = parent_comment
        current_attitude = parent_attitude

        for depth in range(1, max_depth + 1):
            print(f"\n    生成第{depth}层回复:")

            # 根据深度和父评论态度选择回复态度
            reply_attitude = self.select_reply_attitude(current_attitude, depth)

            # 生成回复数量
            reply_count = self.get_reply_count(depth, current_attitude)

            print(f"      回复态度: {reply_attitude.value}")
            print(f"      回复数量: {reply_count}")

            # 调用LVN评论生成
            try:
                replies = generate_lvn_comments(
                    persona=self.user_template["persona"],
                    post_content=self.post_content,
                    attitude_type=reply_attitude,
                    pre_lv_comment=current_comment,
                    expand_count=reply_count,
                    is_human_user=False,  # AI用户
                    retry=3
                )

                if replies:
                    print(f"      生成结果 ({len(replies)}条):")
                    for i, reply in enumerate(replies, 1):
                        print(f"        {i}. {reply}")
                        dialogue_chain.append({
                            "depth": depth,
                            "attitude": reply_attitude.value,
                            "content": reply,
                            "parent": current_comment[:30] + "..."
                        })

                    # 选择一条回复作为下一层的父评论
                    if replies:
                        current_comment = replies[0]  # 选择第一条回复
                        current_attitude = reply_attitude
                else:
                    print(f"      生成失败，停止生成")
                    break

            except Exception as e:
                logger.error(f"生成第{depth}层回复失败: {e}")
                print(f"      生成失败: {e}")
                break

        return dialogue_chain

    def select_reply_attitude(self, parent_attitude: Attitude, depth: int) -> Attitude:
        """
        根据父评论态度选择回复态度
        
        Args:
            parent_attitude: 父评论态度
            depth: 当前深度
            
        Returns:
            Attitude: 回复态度
        """
        # 深度优先策略：优先生成有争议性的讨论
        attitude_mapping = {
            Attitude.PERFECT: [Attitude.NEUTRAL_NEGATIVE, Attitude.NEUTRAL, Attitude.NEUTRAL_POSITIVE],
            Attitude.BAD: [Attitude.NEUTRAL_POSITIVE, Attitude.NEUTRAL, Attitude.NEUTRAL_NEGATIVE],
            Attitude.GOOD: [Attitude.NEUTRAL_NEGATIVE, Attitude.NEUTRAL, Attitude.PERFECT],
            Attitude.NEUTRAL_NEGATIVE: [Attitude.BAD, Attitude.NEUTRAL, Attitude.NEUTRAL_POSITIVE],
            Attitude.NEUTRAL_POSITIVE: [Attitude.NEUTRAL_NEGATIVE, Attitude.NEUTRAL, Attitude.GOOD],
            Attitude.NEUTRAL: [Attitude.NEUTRAL_POSITIVE, Attitude.NEUTRAL_NEGATIVE, Attitude.NEUTRAL]
        }

        possible_attitudes = attitude_mapping.get(parent_attitude, [Attitude.NEUTRAL])

        # 根据深度调整选择策略
        if depth <= 2:
            # 前两层优先选择冲突性态度
            conflict_attitudes = [Attitude.BAD, Attitude.NEUTRAL_NEGATIVE, Attitude.NEUTRAL_POSITIVE, Attitude.PERFECT]
            conflict_choices = [att for att in possible_attitudes if att in conflict_attitudes]
            if conflict_choices:
                return random.choice(conflict_choices)

        # 随机选择
        return random.choice(possible_attitudes)

    def get_reply_count(self, depth: int, attitude: Attitude) -> int:
        """
        根据深度和态度获取回复数量
        
        Args:
            depth: 当前深度
            attitude: 当前态度
            
        Returns:
            int: 回复数量
        """
        # 深度越深，回复数量越少
        if depth == 1:
            return random.randint(2, 3)  # L2: 2-3条
        elif depth == 2:
            return random.randint(1, 2)  # L3: 1-2条
        else:
            return 1  # L4+: 1条

    def test_depth_first_generation(self):
        """测试深度优先自我问答方案"""
        print(" InfluAI LVN评论生成测试 - 深度优先自我问答方案")
        print("=" * 60)

        print(f" 用户模板: {self.user_template['template_name']}")
        print(f" 帖子内容: {self.post_content}")
        print(f" LV1评论总数: {sum(len(comments) for comments in self.lv1_comments.values())}")

        # 1. 选择热门评论和普通评论
        hot_comments, regular_comments = self.select_hot_comments()

        # 2. 为热门评论生成深度对话链
        print("\n" + "=" * 60)
        print(" 热门评论深度对话链生成")
        print("=" * 60)

        hot_dialogue_chains = []
        for i, (comment, attitude, heat_score) in enumerate(hot_comments, 1):
            print(f"\n热门评论 {i}: [{attitude.value}] {comment}")
            print(f"热度分数: {heat_score:.2f}")

            # 热门评论生成更深的对话链 (8层)
            dialogue_chain = self.generate_dialogue_chain(comment, attitude, max_depth=8)
            hot_dialogue_chains.append({
                "parent_comment": comment,
                "parent_attitude": attitude.value,
                "heat_score": heat_score,
                "dialogue_chain": dialogue_chain
            })

        # 3. 为普通评论生成标准深度对话链
        print("\n" + "=" * 60)
        print(" 普通评论标准深度对话链生成")
        print("=" * 60)

        regular_dialogue_chains = []
        for i, (comment, attitude, heat_score) in enumerate(regular_comments, 1):
            print(f"\n普通评论 {i}: [{attitude.value}] {comment}")
            print(f"热度分数: {heat_score:.2f}")

            # 普通评论生成标准深度的对话链 (4层)
            dialogue_chain = self.generate_dialogue_chain(comment, attitude, max_depth=4)
            regular_dialogue_chains.append({
                "parent_comment": comment,
                "parent_attitude": attitude.value,
                "heat_score": heat_score,
                "dialogue_chain": dialogue_chain
            })

        # 4. 统计结果
        self.print_generation_summary(hot_dialogue_chains, regular_dialogue_chains)

        return hot_dialogue_chains, regular_dialogue_chains

    def print_generation_summary(self, hot_chains: List[Dict], regular_chains: List[Dict]):
        """打印生成结果统计"""
        print("\n" + "=" * 60)
        print(" LVN评论生成结果统计")
        print("=" * 60)

        # 热门评论统计
        hot_total_replies = sum(len(chain["dialogue_chain"]) for chain in hot_chains)
        hot_max_depth = max(len(chain["dialogue_chain"]) for chain in hot_chains) if hot_chains else 0

        print(f" 热门评论对话链:")
        print(f"   评论数量: {len(hot_chains)}")
        print(f"   总回复数: {hot_total_replies}")
        print(f"   最大深度: {hot_max_depth}")

        # 普通评论统计
        regular_total_replies = sum(len(chain["dialogue_chain"]) for chain in regular_chains)
        regular_max_depth = max(len(chain["dialogue_chain"]) for chain in regular_chains) if regular_chains else 0

        print(f" 普通评论对话链:")
        print(f"   评论数量: {len(regular_chains)}")
        print(f"   总回复数: {regular_total_replies}")
        print(f"   最大深度: {regular_max_depth}")

        # 总体统计
        total_chains = len(hot_chains) + len(regular_chains)
        total_replies = hot_total_replies + regular_total_replies

        print(f" 总体统计:")
        print(f"   总对话链数: {total_chains}")
        print(f"   总回复数: {total_replies}")
        print(f"   平均每条LV1评论生成回复数: {total_replies / total_chains:.1f}")

        # 态度分布统计
        attitude_counts = {}
        for chain in hot_chains + regular_chains:
            for reply in chain["dialogue_chain"]:
                attitude = reply["attitude"]
                attitude_counts[attitude] = attitude_counts.get(attitude, 0) + 1

        print(f" 回复态度分布:")
        for attitude, count in sorted(attitude_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {attitude}: {count}条")

    def run_test(self):
        """运行测试"""
        try:
            hot_chains, regular_chains = self.test_depth_first_generation()

            print("\n" + "=" * 60)
            print(" 测试完成！")
            print("=" * 60)

            return True

        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            print(f" 测试过程中发生错误: {e}")
            return False


def main():
    """主函数"""
    # 设置环境变量
    os.environ["DB_TYPE"] = "mysql"
    os.environ["MYSQL_HOST"] = "localhost"
    os.environ["MYSQL_PORT"] = "3306"
    os.environ["MYSQL_USER"] = "root"
    os.environ["MYSQL_PASSWORD"] = "influai"
    os.environ["MYSQL_DATABASE"] = "influai"
    os.environ["MYSQL_CHARSET"] = "utf8mb4"

    tester = LVNCommentTester()

    try:
        success = tester.run_test()
        if success:
            print("\n LVN评论生成测试成功完成！")
        else:
            print("\n LVN评论生成测试失败或中断")
    except KeyboardInterrupt:
        print("\n 测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"\n 测试运行失败: {e}")


if __name__ == "__main__":
    main()

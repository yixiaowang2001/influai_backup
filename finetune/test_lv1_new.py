#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI LV1评论生成测试脚本 - Few-shot版本

使用方法：
1. 确保已构建FAISS索引（在finetune/index目录下）
2. 修改POST_CONTENT配置帖子内容
3. 运行脚本：python test_lv1_new.py

功能：
- 生成种子评论（seed comments）
- 使用种子评论作为query检索相似评论
- 将检索结果作为few-shot示例
- 生成扩展评论并打印结果
"""

import json
import os
import sys
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from backend.ai_module.comment_related import generate_lv1_seeds
from backend.ai_module.llm import chat
from backend.ai_module.llm_utils import parse_json_response
from backend.models import Attitude
from backend.utils.logger import get_logger
from finetune.hybrid_search import HybridSearchEngine

logger = get_logger(__name__)

# ============================================================
# 配置部分
# ============================================================
CONFIG = {
    # 帖子内容（可修改）
    'POST_CONTENT': '大家明天都来看我的演唱会！',
    
    # FAISS检索参数
    'FAISS_TOP_K': 5,  # 检索返回的示例数量
    'INDEX_DIR': './index',  # FAISS索引目录
    
    # 评论扩展参数
    'EXPAND_COUNT': 3,  # 每个seed扩展的评论数量
    
    # 用户模板（与test_lv1.py相同）
    'USER_TEMPLATE': {
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
    },
    
    # 历史帖子
    'HISTORY_POSTS': [
        "昨天的工作很充实！",
        "新项目进展顺利",
        "感谢大家的支持"
    ]
}


# ============================================================
# Few-shot Prompt函数
# ============================================================

def get_expand_lv1_comments_prompt_with_fewshot(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: List[str],
        expand_count: int,
        fewshot_examples: List[str]
) -> Tuple[str, str]:
    """
    生成带few-shot示例的评论扩展prompt
    
    Args:
        persona: 用户人设
        post_content: 帖子内容
        attitude_type: 态度类型
        seed_comments: 种子评论列表
        expand_count: 扩展数量
        fewshot_examples: few-shot示例列表
        
    Returns:
        (system_prompt, user_prompt)
    """
    system_prompt = f"""**角色**：社交媒体评论扩展AI，基于种子评论生成同态度/同风格的批量评论
**核心任务**：保持原始评论的核心特征（态度及网络用户风格），生成语义相似的新评论

### 内容生成法则
1. **特征继承机制**
   - 语言风格：严格继承种子评论的网络用语特征
   - 情感强度：保持原始评论的情感烈度
   - 句式结构：与种子评论保持类似的句式结构，但不能完全一致
   - emoji使用（重要！）：在新生成的评论里严禁使用emoji

2. **语义变体策略**
   - 角度偏移：保持态度不变，调整表述视角
   - 句式重组：拆解长句结构或合并短句，保持平均长度±50%波动

3. **相似度控制**
   - 严格维持原始态度分类
   - 禁止完全复制种子句式结构

4. **批量生成规范**
   - 每组种子评论生成{expand_count}条变体
   - 变体间重复度<10%（使用不同修辞范例）
   - 自动过滤涉政/低俗内容

### 输出格式
```json
{{
  "expansions": [
    "变体评论1",
    "变体评论2",
    // 生成{expand_count}条
  ]
}}
```
"""

    # 构建few-shot示例部分
    fewshot_section = "**参考示例（相似评论）**：\n"
    if fewshot_examples:
        for i, example in enumerate(fewshot_examples, 1):
            fewshot_section += f"{i}. {example}\n"
    else:
        fewshot_section += "（无参考示例）\n"

    user_prompt = f"""### 扩展任务指令
请基于以下种子评论批量生成同风格变体：

**用户人设**: {persona}
**目标帖子**："{post_content}"
**原始态度**: {str(attitude_type)}
**生成数量**: {expand_count}
**种子评论组**（共{len(seed_comments)}条）：
{seed_comments}

{fewshot_section}

**执行要求**
1. 参考上述示例的风格和表达方式
2. 每组生成{expand_count}条符合系统约束的变体
3. 严格保持原始态度分类
4. 输出完整JSON结构
"""

    return system_prompt, user_prompt


# ============================================================
# 带Few-shot的评论扩展函数
# ============================================================

def expand_lv1_comments_with_fewshot(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: List[str],
        expand_count: int,
        fewshot_examples: List[str],
        retry: int = 5
) -> List[str]:
    """
    使用few-shot示例扩展一级评论
    
    Args:
        persona: 用户人设
        post_content: 帖子内容
        attitude_type: 态度类型
        seed_comments: 种子评论列表
        expand_count: 扩展数量
        fewshot_examples: few-shot示例列表
        retry: 重试次数
        
    Returns:
        扩展后的评论列表
    """
    logger.info(f"使用few-shot扩展一级评论，态度: {attitude_type}")
    
    system_prompt, user_prompt = get_expand_lv1_comments_prompt_with_fewshot(
        persona=persona,
        post_content=post_content,
        attitude_type=attitude_type,
        seed_comments=seed_comments,
        expand_count=expand_count,
        fewshot_examples=fewshot_examples
    )

    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config_type="comment"
        )
        
        if not response:
            logger.warning(f"收到空的一级评论扩展响应，态度: {attitude_type}，第{i + 1}次尝试")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "expansions" in json_response.keys():
            logger.info(f"成功扩展一级评论（带few-shot），态度: {attitude_type}")
            return json_response["expansions"]
        logger.warning(f"扩展一级评论失败，态度: {attitude_type}，第{i + 1}次重试")
    
    logger.warning(f"扩展一级评论失败，态度: {attitude_type}，未找到有效扩展")
    return []


# ============================================================
# 主测试流程
# ============================================================

class FewShotCommentTester:
    """Few-shot评论生成测试器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.search_engine = None
        self.user_template = config['USER_TEMPLATE']
        self.post_content = config['POST_CONTENT']
        
    def load_search_engine(self):
        """加载FAISS检索引擎"""
        print("=" * 60)
        print(" 加载FAISS检索引擎")
        print("=" * 60)
        
        try:
            self.search_engine = HybridSearchEngine(
                index_dir=self.config['INDEX_DIR']
            )
            self.search_engine.load_index()
            print(" 检索引擎加载成功！\n")
            return True
        except Exception as e:
            logger.error(f"加载检索引擎失败: {e}")
            print(f" 加载检索引擎失败: {e}")
            return False
    
    def generate_seeds(self) -> Dict[Attitude, List[str]]:
        """生成种子评论"""
        print("=" * 60)
        print(" 生成种子评论")
        print("=" * 60)
        
        try:
            seeds = generate_lv1_seeds(
                persona=self.user_template['persona'],
                post_content=self.post_content,
                history_posts=self.config['HISTORY_POSTS'],
                retry=3
            )
            
            total_seeds = sum(len(comments) for comments in seeds.values())
            print(f" 成功生成 {total_seeds} 条种子评论\n")
            
            return seeds
        except Exception as e:
            logger.error(f"生成种子评论失败: {e}")
            print(f" 生成种子评论失败: {e}")
            return {}
    
    def search_similar_comments(self, query: str, top_k: int) -> List[str]:
        """检索相似评论"""
        try:
            result = self.search_engine.search(
                query=query,
                top_k=top_k,
                verbose=False
            )
            
            # 提取文本内容
            similar_comments = [item['text'] for item in result['results']]
            return similar_comments
        except Exception as e:
            logger.error(f"检索相似评论失败: {e}")
            return []
    
    def process_seed_comment(
        self,
        attitude: Attitude,
        seed_comment: str,
        seed_index: int,
        total_seeds: int
    ):
        """处理单个种子评论"""
        print("\n" + "=" * 60)
        print(f" 处理种子评论 [{seed_index}/{total_seeds}]")
        print("=" * 60)
        print(f" 态度类型: {attitude.value}")
        print(f" 种子评论: {seed_comment}")
        print("-" * 60)
        
        # 1. 检索相似评论
        print(f"\n[1/2] 检索相似评论 (Top {self.config['FAISS_TOP_K']})...")
        fewshot_examples = self.search_similar_comments(
            query=seed_comment,
            top_k=self.config['FAISS_TOP_K']
        )
        
        print(f" 检索到 {len(fewshot_examples)} 条相似评论：")
        for i, example in enumerate(fewshot_examples, 1):
            print(f"   {i}. {example}")
        
        # 2. 使用few-shot扩展评论
        print(f"\n[2/2] 生成扩展评论 (数量: {self.config['EXPAND_COUNT']})...")
        expanded_comments = expand_lv1_comments_with_fewshot(
            persona=self.user_template['persona'],
            post_content=self.post_content,
            attitude_type=attitude,
            seed_comments=[seed_comment],
            expand_count=self.config['EXPAND_COUNT'],
            fewshot_examples=fewshot_examples,
            retry=3
        )
        
        print(f" 成功生成 {len(expanded_comments)} 条扩展评论：")
        for i, comment in enumerate(expanded_comments, 1):
            print(f"   {i}. {comment}")
        
        return {
            'attitude': attitude.value,
            'seed': seed_comment,
            'fewshot_examples': fewshot_examples,
            'expanded': expanded_comments
        }
    
    def run_test(self):
        """运行完整测试"""
        print("\n" + "=" * 60)
        print(" InfluAI Few-shot 评论生成测试")
        print("=" * 60)
        print(f" 帖子内容: {self.post_content}")
        print(f" 用户模板: {self.user_template['template_name']}")
        print(f" FAISS Top-K: {self.config['FAISS_TOP_K']}")
        print(f" 扩展数量: {self.config['EXPAND_COUNT']}")
        print("=" * 60 + "\n")
        
        # 1. 加载检索引擎
        if not self.load_search_engine():
            return False
        
        # 2. 生成种子评论
        seeds = self.generate_seeds()
        if not seeds:
            return False
        
        # 3. 处理所有种子评论
        all_results = []
        seed_index = 0
        total_seeds = sum(len(comments) for comments in seeds.values())
        
        for attitude, seed_comments in seeds.items():
            for seed_comment in seed_comments:
                seed_index += 1
                result = self.process_seed_comment(
                    attitude=attitude,
                    seed_comment=seed_comment,
                    seed_index=seed_index,
                    total_seeds=total_seeds
                )
                all_results.append(result)
        
        # 4. 最终统计
        print("\n" + "=" * 60)
        print(" 测试完成")
        print("=" * 60)
        print(f" 处理种子评论数: {len(all_results)}")
        total_expanded = sum(len(r['expanded']) for r in all_results)
        print(f" 生成扩展评论数: {total_expanded}")
        print("=" * 60 + "\n")
        
        # 5. 保存结果
        self.save_results(all_results)
        
        return True
    
    def save_results(self, results: List[Dict]):
        """保存结果到JSON文件"""
        try:
            output_file = os.path.join(
                os.path.dirname(__file__),
                'test_lv1_new_results.json'
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'config': {
                        'post_content': self.post_content,
                        'faiss_top_k': self.config['FAISS_TOP_K'],
                        'expand_count': self.config['EXPAND_COUNT']
                    },
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            
            print(f" 结果已保存到: {output_file}\n")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    """主函数"""
    tester = FewShotCommentTester(CONFIG)
    
    try:
        success = tester.run_test()
        if success:
            print("\n 测试成功完成！")
        else:
            print("\n 测试失败或中断")
    except KeyboardInterrupt:
        print("\n 测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"\n 测试运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


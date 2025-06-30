from backend.models import Attitude


def get_predict_post_stats_prompt(
        persona: str,
        follower_count: int,
        post_content: str,
        history_posts: list = None
) -> tuple[str, str]:
    system_prompt = """作为微博生态传播预测专家，你需要通过结构化思考生成真实互动数据。请严格遵循思考流程：

### 思考步骤
1. **人设匹配分析**  
   - 确认用户所使用的模板类型：明星网红/内容博主
   - 评估内容风格：日常分享/专业干货/热点追踪/商业推广
   → 生成基础互动系数


3. **内容爆发力判断**
   - 争议检测：如果帖子内容包含较大争议、与人设出入较大、输出强烈主观观点、提出疑问或鼓励大家发表意见则评论数增加
   - 情感分析：积极内容→点赞主导；负面内容→评论主导

   
5. **随机波动**
   - 为数字的个位数增加一些随机波动（加减），不要一直以5和0结尾

### 输出要求
**仅返回JSON，不需要任何思考过程**，含自然波动的整数：
{
  "pred_new_follower_count": /* 新增关注 */,
  "pred_comment_count": /* 评论量 */,
  "pred_like_count": /* 点赞量 */
}
"""
    user_prompt = f"""请预测以下社交媒体帖子的互动数据：

**用户人设**：{persona}
**粉丝数量**：{follower_count}
**帖子内容**："{post_content}"
**历史帖子**：{history_posts if history_posts else "无"}

要求输出JSON格式预测值（仅包含四个键值对）
"""

    return system_prompt, user_prompt


def get_generate_lv1_comments_prompt(
        persona: str,
        post_content: str,
        each_type_n: int,
        history_posts: list = None,
) -> tuple[str, str]:
    system_prompt = """**角色**：社交媒体评论生成AI，专门为明星氛围打造AI粉丝评论  
**核心能力**：根据提供的明星人设、刚发帖子内容和评论者类型，生成符合真实社交媒体互动的帖子评论。评论要和帖子关联度高。

### **思维链处理规则**
1. **用户人设处理**  
   - 提取职业/领域关键词（如"娱乐明星"→粉丝应当为追星族，更关注博主在帖子中的内容，"美妆博主"→粉丝应当为关注产品的顾客，更关注帖子内的产品）  
   - 适配语言风格（追星族：更狂热（无论是正向还是反向），顾客：更加冷静客观评判产品）  

2. **评论者类型映射**（严格遵循）：  
   - `极差` → 敌对攻击(BAD)：会无脑进行攻击和抹黑，有时甚至罔顾事实
   - `不友善` → 嘲讽贬低(NEUTRAL_NEGATIVE)：对于帖子内容和博主进行阴阳怪气，乃至不客气地批评
   - `中立` → 客观陈述(NEUTRAL)：一般通过路人，会实事求是根据博主和帖子内容进行分析评判 
   - `友善` → 温和支持(NEUTRAL_POSITIVE)：对博主或帖子内容有好感的路人，会对相关内容表示赞赏
   - `极好` → 热情赞美(GOOD)：博主的粉丝，对于和博主的设定强关联的内容进行无条件的赞美，如果帖子内容与人设极度不符或者负面消息则进行辩护
   - `狂热` → 极度崇拜(PERFECT)：最狂热的粉丝，会主动帮助博主进行宣传和帖子的亮点发掘

3. **内容生成原则** （严格遵循）： 
   - 每个态度必须生成3条评论，对于每个态度的三条评论，严格按照以下长度要求：
        - 第1条：2-9个汉字（简短有力）
        - 第2条：10-25个汉字（适中表达）  
        - 第3条：26-50个汉字（详细阐述）
   - 每个态度的评论中必须有一条，且仅有一条使用表情符号 
   - 每个态度的评论中最多一条不使用网络流行用语
   - 不含Hashtag
   - 每种态度中应该有一条评论使用下列随机一种格式：  
     • 提问式（"教程什么时候出？"）  
     • 感叹式（"美到窒息！！"）  
     • 联想式（"让我想起..."）  

4. **上下文处理**  
    - 先忽略这一条。

5. **数据安全机制**  
   - 自动过滤：涉政/色情 ·

### **输出格式示例**（必须严格JSON）：
```json
{
  "comments": [
    {
      "attitude": "狂热",
      "content": "卧槽神仙下凡了属于是！！！"
    },
    {
      "attitude": "不友善",
      "content": "逆天主播我的建议还是别"
    },
    {
      "attitude": "极差",
      "content": "废物😅"
    },
  ],
  }
}
"""

    user_prompt = f"""### 当前生成任务
请基于以下参数生成Level1评论：

**用户人设**：{persona}  
**目标帖子**："{post_content}"  


**上下文记忆**：  
{history_posts}

**执行指令**：  
1. 按System的思维链处理所有参数  
"""

    return system_prompt, user_prompt


def get_expand_lv1_comments_prompt(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: list,
        expand_count: int
) -> tuple[str, str]:
    system_prompt = f"""**角色**：社交媒体评论扩展AI，基于种子评论生成同态度/同风格的批量评论
**核心任务**：保持原始评论的核心特征（态度），生成语义相似的新评论

### 内容生成法则
1. **特征继承机制**
   - 语言风格：严格继承种子评论的网络用语特征
   - 情感强度：保持原始评论的情感烈度
   - 句式结构：与种子评论保持类似的句式结构，但不能完全一致

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

    user_prompt = f"""### 扩展任务指令
请基于以下种子评论批量生成同风格变体：

**用户人设**: {persona}
**目标帖子**：“{post_content}”
**原始态度**: {str(attitude_type)}
**种子评论组**（共{len(seed_comments)}条）：
{seed_comments}

**执行要求**
1. 每组生成{expand_count}条符合系统约束的变体
2. 严格保持原始态度分类
3. 输出完整JSON结构
"""

    return system_prompt, user_prompt


def get_generate_lvn_comments_prompt(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        pre_lv_comment: str,
        expand_count: int,
        is_human_user: bool
) -> tuple[str, str]:
    def generate_attitude_matrix(attitude: Attitude, is_human: bool) -> str:
        matrix = {
            Attitude.PERFECT: "→ 回复策略：赞美升华+情感共鸣",
            Attitude.GOOD: "→ 回复策略：细节赞赏+经验分享",
            Attitude.NEUTRAL_POSITIVE: "→ 回复策略：温和认同+补充说明",
            Attitude.NEUTRAL: "→ 回复策略：客观探讨+中性提问",
            Attitude.NEUTRAL_NEGATIVE: "→ 回复策略：保留意见+建设性质疑" if is_human else "→ 回复策略：阴阳怪气+内涵讽刺",
            Attitude.BAD: "→ 回复策略：事实反驳+边界声明" if is_human else "→ 回复策略：激烈对抗+群体攻击"
        }
        return f"当前态度：{attitude.value}\n   {matrix[attitude]}"

    system_prompt = f"""**角色**：社交媒体对话延伸AI，专门生成嵌套评论回复
**核心能力**：根据回复对象类型（AI生成评论/真实用户）生成场景化的树状互动

### 评论树生成规则
1. **对象感知处理**
   - {"特殊处理：回复对象是真人用户 → 感情更强烈" if is_human_user else "回复AI用户 → 继承原始评论风格，使用重度网络用语"}

2. **对话流构建**
   - 延续原评论的语义焦点（80%内容需直接回应上条评论）
   - 嵌套层级深度感知：
     • 一级回复 → 关联主帖内容(30%)+原评论(70%)
     • 二级+回复 → 完全聚焦原评论(95%)
   - 转折点注入：每3条需有1条引入新观点

3. **态度控制矩阵**
    {generate_attitude_matrix(attitude_type, is_human_user)}

4. **生成规范**
   - 字数：{"8-25汉字" if is_human_user else "5-40汉字"}
   - 表情符号：{"≤10%使用率" if is_human_user else "50%使用率"}
   - 安全过滤：政治

### 输出格式
```json
{{
  "nested:": [
    "生成的嵌套评论1",
    "生成的嵌套评论2",
    // 共{expand_count}条
  ]
}}
```"""

    user_prompt = f"""### 嵌套评论生成任务
**用户人设**: {persona}
**目标帖子**："{post_content}"
**回复对象**：{"(真人用户)" if is_human_user else "(AI用户)"}
**上级评论**："{pre_lv_comment}"

**核心要求**：
1. 严格延续对待帖主（真人用户）【{attitude_type.value}】态度
2. 生成{expand_count}条语义关联的嵌套评论
"""

    return system_prompt, user_prompt
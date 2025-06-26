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

要求输出JSON格式预测值（仅包含四个键值对）"""

    return system_prompt, user_prompt


def get_generate_lv1_comments_prompt(
        persona: str,
        post_content: str,
        commenter_distribution: dict,
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

3. **内容生成原则**  
   - 字数：10～50个汉字（生成字数长短变化幅度大一些）
   - 70%的评论不含表情符号 
   - 80%的评论都使用网络社交用语
   - 不含表情符号
   - 每3条覆盖1种互动形式：  
     • 提问式（"教程什么时候出？"）  
     • 感叹式（"美到窒息！！"）  
     • 联想式（"让我想起..."）  

4. **上下文处理**  
   - 当有历史帖子时，选取最近3条建立关联（例："比上次的xx改进好多！"）  
   - 时间衰减权重：3天内内容权重0.8，1周前0.3  

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
}"""

    user_prompt = f"""### 当前生成任务
请基于以下参数生成Level1评论：

**用户人设**：{persona}  
**目标帖子**："{post_content}"  

**评论要求**：  
1. 需要生成的评论态度类型：{commenter_distribution.keys()}  
2. 每类生成数量：{each_type_n}条  

**上下文记忆**：  
{history_posts}

**执行指令**：  
1. 按System的思维链处理所有参数  
2. 对"狂热"类型使用专属称呼库"""

    return system_prompt, user_prompt


def get_expand_lv1_comments_prompt(
        post_content: str,
        attitude_type: Attitude,
        reference_lv1_list: list,
        generate_number: int
) -> tuple[str, str]:
    system_prompt = """
    """

    user_prompt = """
    """

    return system_prompt, user_prompt


def get_generate_lvn_comments_prompt(
        post_content: str,
        pre_lv_comment: str,
        attitude_type: Attitude,
        generate_number: int
) -> tuple[str, str]:
    system_prompt = """
    """

    user_prompt = """
    """

    return system_prompt, user_prompt

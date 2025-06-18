def get_predict_post_stats_prompt(
        persona: str,
        follower_count: int,
        post_content: str,
        history_posts: list = None
) -> tuple[str, str]:

    system_prompt = """你是社交媒体分析专家，专门预测用户帖子的互动数据。请根据以下规则分析输入并预测帖子的传播效果：
1. **输出格式**：返回标准的 **JSON 对象**，包含这四个整数值：
   - `pred_repost_count` (预测转发量)
   - `pred_new_follower_count` (预测新增关注量)
   - `pred_comment_count` (预测评论量)
   - `pred_like_count` (预测点赞量)
2. **分析框架**：
   - **人设匹配度**：评估帖子内容与用户人设的一致性（匹配度越高，互动越强）
   - **粉丝基数**：根据粉丝数按比例缩放预测值（10万粉丝 ≠ 1000万粉丝）
   - **历史参照**：若有历史帖子，分析其互动规律作为参考
   - **内容爆发力**：检测关键词（如"独家"、"抽奖"、"紧急"）和情感倾向
3. **处理原则**：
   - 若信息不足则采用保守预测（所有值 ≥0）
   - 禁止任何解释性文字，仅输出JSON格式结果"""

    user_prompt = f"""请预测以下社交媒体帖子的互动数据：

**用户人设**：{persona}
**粉丝数量**：{follower_count}
**帖子内容**："{post_content}"
**历史帖子**：{history_posts if history_posts else "无"}

要求输出JSON格式预测值（仅包含四个键值对）"""

    return system_prompt, user_prompt

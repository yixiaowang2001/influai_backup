# influai_backup

## TODO
1. AI_module完成
   1. generate_human_user_post_data: 基于人类用户人设、粉丝量、发帖的内容、历史帖子（及相关信息：发帖时间、上一条帖子发帖时间间隔、转发、评论、点赞数量），预测用户当前的帖子会有多少转发、评论、点赞数量。
   2. generate_human_user_post_comments: 基于人类用户人设、粉丝分布、评论数量、发帖的内容、历史帖子，模拟用户当前的帖子会有哪些评论（及相关信息：点赞数量）
   3. generate_similar_ai_user_comments:
   基于人类用户发帖的内容和AI用户的评论，生成相似评论。
   4. generate_ai_user_sub_comments:
   基于人类用户发帖的内容和AI用户的评论，生成子评论（评论AI用户的评论）。考虑到多样性，可以有黑粉、狂粉等。
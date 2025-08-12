# influai_backup

## TODO
- 接口
  - 4
    - 测试接口（没有current user生成不了，逻辑通过；等待测试正式的发布帖子的逻辑验证）
  - 5
  - 6
  - 7
- 请求速度优化

## BUG
1. 可能存在： 
```bash
2. 2025-08-12 08:48:45,695 [ERROR] backend.main - 生成评论失败: empty range in randrange(1, 1)
2025-08-12 08:48:45,699 [ERROR] backend.main - 错误详情: Traceback (most recent call last):
  File "/Users/wangyixiao/Desktop/Files/Projects/influai_backup/backend/main.py", line 279, in generate_comments_for_post
    stats = post_service.generate_comments_for_existing_post(post_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/wangyixiao/Desktop/Files/Projects/influai_backup/backend/services/post_service.py", line 317, in generate_comments_for_existing_post
    expanded_comments = self.expand_lv1_comments_by_attitude(att, comment_count)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/wangyixiao/Desktop/Files/Projects/influai_backup/backend/services/post_service.py", line 227, in expand_lv1_comments_by_attitude
    short_num = rand_int(num / 3)
                ^^^^^^^^^^^^^^^^^
  File "/Users/wangyixiao/Desktop/Files/Projects/influai_backup/backend/utils/global_utils.py", line 26, in rand_int
    return random.randint(low_bound, high_bound)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/influai/lib/python3.12/random.py", line 336, in randint
    return self.randrange(a, b+1)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/influai/lib/python3.12/random.py", line 319, in randrange
    raise ValueError(f"empty range in randrange({start}, {stop})")
ValueError: empty range in randrange(1, 1)
```

## CoT
- 维护一个AI用户的数据库，包含生成的userid，username，态度，创建时间，是否是粉丝。 
  - 总数取决于粉丝初始量，设定为粉丝量为2倍。
  - 初始用户分布：先选取一部分作为粉丝，另一部分非粉丝默认为中立态度。
  - 对于粉丝用户，取决于一开始自然语言设定的分布（或者是结构化输入，比如："狂热": 10%的用户）
  - 态度本质上是一个小数（比如-1～-0.7是很不认同，0.7～1是非常认可）。态度越大，以后评论的概率越高（在每个态度区间内，可能得用比较skewed的distribution，不能uniform，当然也不要太skewed）。对于普通用户（态度=0），评论概率就是随机的。
- 综合来说，数据库包括人类用户信息、帖子信息、评论信息、AI用户信息
  - 帖子信息主要来源于人类用户。
  - 评论信息维护几个字段：
    - 评论时间
    - 评论方（人类、AI）
    - 评论者userid
    - 如果评论方是AI，则有态度（这个态度与AI的设定吻合）
    - 评论层级：l1、l2
    - 回复评论的id：如果是l1，则没有；如果l2，则是l1

## 总结
- AI用户态度是不变的，每个AI用户也并没有相关经历
- 但是每条评论是可以指派给每个特定AI用户的（通过这种反向分配的策略，减少AI的互动量，降低交互成本）

## lv2逻辑
- AI筛选lv1评论（筛选出5条情绪最强烈：最好的、最坏的），进行硬编码限制
- 丢给AI，让AI打分，让AI决定点赞数；根据成本，实际体验，给特别高的高赞数
- 根据AI生成的评论，生成lv2

## Notes
生成requirements.txt
```bash
pipreqs . --encoding=utf-8 --force
```
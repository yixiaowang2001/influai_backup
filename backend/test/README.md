# InfluAI 评论生成测试工具

现在breath和depth的基础代码和格式已经调整好了，在test目录下。

具体开始流程如下：
- 首先启动后端，通过API docs进行角色创建和一条帖子的发表。
- 等待评论推送完成（目前设计的是30s推送结束，应该很快）。推送结束后，可以运行test select来看一下筛选效果。
- 推送完毕后，关闭服务，直接运行test lvn depth和test lvn breath就行。具体帖子内容、上级评论内容、态度，都会打印出来。
- 可以通过修改参数来选择不同的一级评论来测试：
- 
```python
parameters = get_test_parameters(post_id=1, parent_comment_id=1, comment_count=87)
```

当前问题（需要调整prompt）：
- 态度不一致：大模型一直不能理解态度不是对上级评论的态度，是对博主的态度
- 说话比较人机，不够激进且具有攻击性
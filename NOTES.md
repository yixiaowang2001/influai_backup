# influai_backup

## TODO
- 基础
  - 实现页面动态更新
  - 实现推送提醒
- 完善
  - 点赞逻辑
  - 点赞推送
  - UI迭代
  - lvn评论

## 未来TODO
- 整体内容讨论，包括还需要什么功能界面，先lvn、调优还是上云
- 产品路线（用户使用场景和整体目标）
- 评论风格优化

## BUG
- 人设模版（和粉丝数量不匹配）- 成长这一块
- prompt：如果用户发一些无意义内容，生成的评论会很人机

## Notes

### 1. 生成requirements.txt
```bash
pipreqs . --encoding=utf-8 --force
```

### 2. 删除数据库
```bash
mysql -u root -p
```

```mysql
DROP DATABASE influai;
```

```mysql
SHOW DATABASES;
```

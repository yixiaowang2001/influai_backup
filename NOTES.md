# influai_backup

## TODO
- 上云
  - 每一种不同的生成应该是异步（lv1、lvn）
  - 生成和查询应该是异步的
  - 每个查询需要解偶（点赞是点赞、内容是内容）
- 点赞相关
  - 人类用户发帖点赞推送（固定间隔）
  - 人类用户发评论点赞推送（固定间隔）
  - AI用户评论点赞预研
- 推送
  - 固定间隔推送逻辑完成
- 筛选热门评论
  - 筛选参数调整（短的坏评论，情绪强度？bert）
  - 筛选热门评论链接数据库
- lvn评论
  - lvn prompt调整（格式不对）
  - lvn评论链接数据库
  - lvn评论添加进服务
  - lvn评论接口

## BUG
- 人设模版（和粉丝数量不匹配）- 成长这一块
- prompt：如果用户发一些无意义内容，生成的评论会很人机

## 未来TODO
- 接口开发
  - 删除human_user

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

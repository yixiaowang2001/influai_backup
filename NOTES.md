# influai_backup

## TODO
- 上云
- 点赞相关
- 推送相关
- lvn评论相关
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

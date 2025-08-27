# influai_backup

## TODO
- 推送
- 上云
- 推送（生成逻辑异步）
- L2评论

## BUG

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

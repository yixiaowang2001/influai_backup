# 发布帖子接口文档 (3.2)

## 概述

发布帖子接口实现了完整的帖子发布流程，包括：
1. 发布帖子到数据库
2. 根据当前用户的user_template_id获取对应的人设
3. 使用AI生成对应的数据（点赞数、评论数等）
4. 生成对应的评论并插入数据库
5. 通过WebSocket实时推送更新

## 全局用户管理

为了避免每个接口都传入human_user，系统实现了全局用户管理机制：

### 设置当前用户
```http
POST /user/set-current
Content-Type: application/json

{
    "human_user_id": 1
}
```

**响应：**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "humanUserId": 1,
        "humanUsername": "测试用户",
        "userTemplateId": 1,
        "message": "当前用户设置成功"
    }
}
```

### 获取当前用户
```http
GET /user/current
```

### 清除当前用户
```http
DELETE /user/current
```

## 发布帖子接口

### 接口信息
- **URL**: `POST /posts`
- **Content-Type**: `application/json`

### 请求参数
```json
{
    "content": "这是帖子内容，不能超过140字符"
}
```

### 响应格式
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": "post_123",
        "content": "这是帖子内容",
        "author": {
            "id": "user_1",
            "username": "测试用户",
            "userId": "@测试用户"
        },
        "timestamp": "2024-01-01T12:00:00",
        "createdAt": "2024-01-01T12:00:00.000000",
        "likes": 0,
        "commentsCount": 0,
        "isLiked": false
    }
}
```

## 完整流程示例

### 1. 设置当前用户
```bash
curl -X POST "http://localhost:8000/user/set-current" \
     -H "Content-Type: application/json" \
     -d '{"human_user_id": 1}'
```

### 2. 发布帖子
```bash
curl -X POST "http://localhost:8000/posts" \
     -H "Content-Type: application/json" \
     -d '{"content": "这是一条测试帖子！"}'
```

### 3. 获取帖子评论
```bash
curl "http://localhost:8000/posts/123/comments"
```

## 技术实现细节

### PostService 类
- 负责处理帖子的创建和评论生成
- 支持通过template_name或template_id初始化
- 包含完整的AI评论生成逻辑

### 评论生成流程
1. **基础更新**: 预测帖子统计数据（点赞数、评论数等）
2. **生成种子评论**: 为不同态度类型生成种子评论
3. **扩展评论**: 根据态度分布扩展评论数量
4. **分配AI用户**: 为每条评论分配合适的AI用户
5. **插入数据库**: 将评论保存到数据库

### WebSocket 实时推送
- 新帖子发布时推送帖子信息
- 评论生成完成后推送评论数更新
- 点赞时推送点赞数更新

## 错误处理

### 常见错误
- `400`: 帖子内容为空或超过140字符
- `400`: 未设置当前用户
- `500`: 服务器内部错误

### 错误响应格式
```json
{
    "detail": "错误描述信息"
}
```

## 测试

使用提供的测试脚本验证完整流程：

```bash
python test_post_flow.py
```

测试脚本会：
1. 获取所有用户
2. 设置当前用户
3. 发布测试帖子
4. 等待评论生成
5. 获取评论列表
6. 验证更新后的帖子信息

## 注意事项

1. **用户设置**: 发布帖子前必须先设置当前用户
2. **内容限制**: 帖子内容不能超过140字符
3. **异步处理**: 评论生成是异步的，可能需要几秒钟
4. **WebSocket**: 建议使用WebSocket监听实时更新
5. **错误处理**: 评论生成失败不会影响帖子发布

## 相关接口

- `GET /user/profile` - 获取所有用户
- `GET /posts` - 获取帖子列表
- `GET /posts/{post_id}/comments` - 获取帖子评论
- `POST /posts/{post_id}/like` - 点赞帖子
- `POST /comments/{comment_id}/like` - 点赞评论 
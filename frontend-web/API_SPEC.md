# InfluAI Frontend-Backend API 接口文档

## 1. 通用响应格式
```json
{
  "code": 200,
  "message": "success", 
  "data": {}
}
```

---

## 2. 用户相关接口

### 2.1 获取当前用户信息
**GET** `/user/profile`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "user_12345",
    "username": "默认用户",
    "userId": "@example_user",
    "template": "用户模版内容"
  }
}
```

---

## 3. 帖子相关接口

### 3.1 获取帖子列表（时间线）
**GET** `/posts`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "post_67890",
      "content": "这是一条测试帖子",
      "author": {
        "id": "user_12345", 
        "username": "默认用户",
        "userId": "@example_user"
      },
      "timestamp": "刚刚",
      "createdAt": "2024-01-15T10:30:00Z",
      "likes": 5,
      "commentsCount": 3,
      "isLiked": false
    }
  ]
}
```

### 3.2 发布帖子
**POST** `/posts`

**请求体:**
```json
{
  "content": "帖子内容，最多140字符"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "post_67891",
    "content": "帖子内容，最多140字符",
    "author": {
      "id": "user_12345",
      "username": "默认用户", 
      "userId": "@example_user"
    },
    "timestamp": "刚刚",
    "createdAt": "2024-01-15T10:35:00Z",
    "likes": 0,
    "commentsCount": 0,
    "isLiked": false
  }
}
```

### 3.3 点赞帖子
**POST** `/posts/{postId}/like`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "postId": "post_67890",
    "likes": 6
  }
}
```

---

## 4. 评论相关接口

### 4.1 获取帖子评论列表
**GET** `/posts/{postId}/comments`

**查询参数:**
- `sort`: 排序方式（time: 按时间, likes: 按点赞数，默认time）

**响应示例:**
```json
{
  "code": 200,
  "message": "success", 
  "data": [
    {
      "id": "comment_11111",
      "content": "这是一条评论",
      "author": {
        "id": "user_12345",
        "username": "默认用户",
        "userId": "@example_user"
      },
      "timestamp": "2分钟前",
      "createdAt": "2024-01-15T10:40:00Z",
      "likes": 2,
      "isLiked": false
    }
  ]
}
```

### 4.2 发布评论
**POST** `/posts/{postId}/comments`

**请求体:**
```json
{
  "content": "评论内容，最多140字符"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "comment_11112", 
    "content": "评论内容，最多140字符",
    "author": {
      "id": "user_12345",
      "username": "默认用户",
      "userId": "@example_user"
    },
    "timestamp": "刚刚",
    "createdAt": "2024-01-15T10:45:00Z",
    "likes": 0,
    "isLiked": false
  }
}
```

### 4.3 点赞评论
**POST** `/comments/{commentId}/like`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "commentId": "comment_11111",
    "likes": 3
  }
}
```

---

## 5. 实时更新机制

### 5.1 WebSocket 连接
**WebSocket** `/ws/updates`

### 5.2 推送消息格式

#### 5.2.1 帖子点赞更新
```json
{
  "type": "post_like_update",
  "data": {
    "postId": "post_67890",
    "likes": 6
  }
}
```

#### 5.2.2 新评论推送
```json
{
  "type": "new_comment",
  "data": {
    "postId": "post_67890",
    "comment": {
      "id": "comment_11113",
      "content": "新的评论内容",
      "author": {
        "id": "user_54321",
        "username": "其他用户",
        "userId": "@other_user"
      },
      "timestamp": "刚刚",
      "createdAt": "2024-01-15T10:50:00Z",
      "likes": 0,
      "isLiked": false
    },
    "commentsCount": 4
  }
}
```

#### 5.2.3 评论点赞更新
```json
{
  "type": "comment_like_update",
  "data": {
    "commentId": "comment_11111",
    "postId": "post_67890", 
    "likes": 4
  }
}
```

#### 5.2.4 帖子评论数更新
```json
{
  "type": "post_comments_update",
  "data": {
    "postId": "post_67890",
    "commentsCount": 5
  }
}
```

---

## 6. 数据模型

### 6.1 用户模型
```json
{
  "id": "string",        // 用户唯一标识
  "username": "string",  // 用户名
  "userId": "string",    // 用户ID（如@example_user）
  "template": "string"   // 用户模版
}
```

### 6.2 帖子模型
```json
{
  "id": "string",           // 帖子唯一标识
  "content": "string",      // 帖子内容
  "author": "User",         // 作者信息
  "timestamp": "string",    // 格式化的时间显示（如"刚刚"、"2分钟前"）
  "createdAt": "string",    // 创建时间（ISO 8601格式，用于排序）
  "likes": "number",        // 点赞数
  "commentsCount": "number", // 评论数
  "isLiked": "boolean"      // 当前用户是否已点赞
}
```

### 6.3 评论模型
```json
{
  "id": "string",        // 评论唯一标识
  "content": "string",   // 评论内容
  "author": "User",      // 作者信息
  "timestamp": "string", // 格式化的时间显示
  "createdAt": "string", // 创建时间（用于排序）
  "likes": "number",     // 点赞数
  "isLiked": "boolean"   // 当前用户是否已点赞
}
```

---

## 7. 接口调用时序

### 7.1 页面初始化
1. `GET /user/profile` - 获取用户信息
2. `GET /posts` - 获取时间线帖子列表
3. 建立 WebSocket 连接

### 7.2 发布帖子
1. `POST /posts` - 发布帖子
2. 后端通过 WebSocket 推送新帖子给其他用户

### 7.3 查看帖子详情
1. 点击帖子进入详情页
2. `GET /posts/{postId}/comments?sort=time` - 获取评论列表

### 7.4 发布评论
1. `POST /posts/{postId}/comments` - 发布评论
2. 后端通过 WebSocket 推送新评论和帖子评论数更新

### 7.5 点赞操作
1. `POST /posts/{postId}/like` 或 `POST /comments/{commentId}/like`
2. 后端通过 WebSocket 推送点赞数更新

---

## 8. 实现说明

### 8.1 时间处理
- 后端返回两个时间字段：
  - `timestamp`: 前端直接显示的格式化时间（如"刚刚"、"2分钟前"）
  - `createdAt`: ISO 8601 格式，用于前端排序和实时更新时间显示

### 8.2 点赞机制
- 每个帖子/评论只能点赞一次，不能取消
- 前端通过 `isLiked` 字段判断是否已点赞
- 已点赞的帖子/评论不响应再次点赞请求

### 8.3 排序功能
- 评论支持按时间和按点赞数排序
- 前端通过 `sort` 参数指定排序方式
- 默认按时间排序（最新在上）

### 8.4 实时更新
- WebSocket 推送不定时的点赞和评论更新
- 前端需要根据推送消息更新对应的UI
- 推送消息包含完整的数据，前端直接替换即可 
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

## 2. 人类用户相关接口

### 2.1 获取所有人类用户信息
**GET** `/user/profile`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "humanUserId": 1,
      "humanUsername": "默认主要用户",
      "avatarPath": "test_path/test.jpg",
      "followerCount": 0,
      "userTemplateId": 1,
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 2.2 获取特定人类用户信息
**GET** `/user/profile/{humanUserId}`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "humanUserId": 1,
    "humanUsername": "默认主要用户",
    "avatarPath": "test_path/test.jpg",
    "followerCount": 0,
    "userTemplateId": 1,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

### 2.3 获取当前用户信息
**GET** `/user/current`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "humanUserId": 1,
    "humanUsername": "默认主要用户",
    "avatarPath": "test_path/test.jpg",
    "followerCount": 0,
    "userTemplateId": 1,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

### 2.4 设置当前用户（通过用户ID）
**POST** `/user/set-current`

**请求体:**
```json
{
  "human_user_id": 1
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "humanUserId": 1,
    "humanUsername": "STAR用户",
    "userTemplateId": 1,
    "message": "当前用户设置成功，已创建 2000000 个AI用户"
  }
}
```

**说明:**
- 设置当前用户后，如果该用户没有对应的AI用户，系统会自动根据用户模板创建AI用户
- AI用户数量为人类用户粉丝数的2倍
- 每个人类用户都有独立的AI用户群体
- 同时只能有一个当前用户，设置新用户会覆盖之前的用户

---

## 3. 用户模板相关接口

### 3.1 获取用户模板列表
**GET** `/user-templates`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "STAR",
      "persona": "明星用户，拥有大量粉丝，影响力强",
      "follower_count": 1000000,
      "commenter_distribution": {
        "positive": 0.6,
        "neutral": 0.3,
        "negative": 0.1
      },
      "default_avatar_path": "/avatars/star.jpg"
    }
  ]
}
```

---

## 4. 帖子相关接口

### 4.1 获取最近帖子列表
**GET** `/posts`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "postId": 1,
      "postContent": "这是一条测试帖子",
      "authorInfo": {
        "id": "user_12345", 
        "username": "默认用户",
        "avatarPath": "test_path/test.jpg"
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

### 4.2 发布帖子
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
    "postId": 1
  }
}
```

### 4.3 点赞帖子
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

## 5. 评论相关接口

### 5.1 获取帖子评论列表
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

### 5.2 发布评论
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
      "id": "human_1",
      "username": "STAR用户",
      "userId": "@star用户"
    },
    "timestamp": "刚刚",
    "createdAt": "2024-01-15T10:45:00Z",
    "likes": 0,
    "isLiked": false
  }
}
```

**说明:**
- 发布评论需要先设置当前用户
- 评论作者为当前设置的人类用户
- AI用户会自动为帖子生成评论，无需手动发布

### 5.3 点赞评论
**POST** `/comments/{commentId}/like`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "commentId": "comment_11111",
    "likes": 3,
    "isLiked": true
  }
}
```

---

## 6. 点赞信息查询接口

### 6.1 批量获取帖子点赞信息
**POST** `/posts/likes-stats`

**请求体:**
```json
{
  "post_ids": ["post_1", "post_2", "post_3"]
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "post_1": {
      "likes": 10,
      "isLiked": true
    },
    "post_2": {
      "likes": 5,
      "isLiked": false
    },
    "post_3": {
      "likes": 0,
      "isLiked": false
    }
  }
}
```

### 6.2 获取单个帖子点赞信息
**GET** `/posts/{postId}/likes`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "postId": "post_1",
    "likes": 10,
    "isLiked": true
  }
}
```

### 6.3 批量获取评论点赞信息
**POST** `/comments/likes-stats`

**请求体:**
```json
{
  "comment_ids": ["comment_1", "comment_2", "comment_3"]
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "comment_1": {
      "likes": 8,
      "isLiked": false
    },
    "comment_2": {
      "likes": 3,
      "isLiked": true
    },
    "comment_3": {
      "likes": 0,
      "isLiked": false
    }
  }
}
```

### 6.4 获取单个评论点赞信息
**GET** `/comments/{commentId}/likes`

**响应示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "commentId": "comment_1",
    "likes": 8,
    "isLiked": false
  }
}
```

**说明:**
- 批量接口一次最多支持50个ID的查询
- 点赞信息包括点赞总数和当前用户是否已点赞
- 如果当前用户未设置，`isLiked` 始终为 `false`

---

## 7. 实时更新机制

### 7.1 WebSocket 连接
**WebSocket** `/ws/updates`

### 7.2 推送消息格式

#### 7.2.1 帖子点赞更新
```json
{
  "type": "post_like_update",
  "data": {
    "postId": "post_67890",
    "likes": 6
  }
}
```

#### 7.2.2 新评论推送
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

#### 7.2.3 评论点赞更新
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

#### 7.2.4 帖子评论数更新
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

## 8. 数据模型

### 8.1 用户模型
```json
{
  "id": "string",        // 用户唯一标识
  "username": "string",  // 用户名
  "userId": "string",    // 用户ID（如@example_user）
  "template": "string"   // 用户模版
}
```

### 8.2 帖子模型
```json
{
  "id": "string",           // 帖子唯一标识
  "content": "string",      // 帖子内容
  "author": "User",         // 作者信息
  "timestamp": "string",    // 格式化的时间显示（如"刚刚"、"2分钟前"）
  "createdAt": "string",    // 创建时间（ISO 8601格式，用于排序）
  "commentsCount": "number"  // 评论数
}
```

### 8.3 评论模型
```json
{
  "id": "string",        // 评论唯一标识
  "content": "string",   // 评论内容
  "author": "User",      // 作者信息（AI用户或人类用户）
  "timestamp": "string", // 格式化的时间显示
  "createdAt": "string"  // 创建时间（用于排序）
}
```

### 8.4 点赞信息模型
```json
{
  "likes": "number",     // 点赞总数
  "isLiked": "boolean"   // 当前用户是否已点赞
}
```

**作者信息说明:**
- AI用户评论：`author.id` 为AI用户ID，`author.username` 为AI用户名
- 人类用户评论：`author.id` 为 `human_用户ID`，`author.username` 为人类用户名

---

## 9. 接口调用时序

### 9.1 页面初始化
1. `GET /user/profile` - 获取所有人类用户信息
2. `GET /user-templates` - 获取用户模板列表
3. `GET /posts` - 获取时间线帖子列表
4. `POST /posts/likes-stats` - 批量获取帖子点赞信息
5. 建立 WebSocket 连接

### 9.2 选择角色并初始化
1. `POST /user/set-current` - 设置当前用户（会自动创建对应的AI用户）
2. 等待初始化完成，准备生成评论

### 9.3 发布帖子
1. `POST /posts` - 发布帖子
2. `GET /posts/{postId}/likes` - 获取新帖子点赞信息
3. 后端通过 WebSocket 推送新帖子给其他用户

### 9.4 查看帖子详情
1. 点击帖子进入详情页
2. `GET /posts/{postId}/comments?sort=time` - 获取评论列表
3. `POST /comments/likes-stats` - 批量获取评论点赞信息

### 9.5 发布评论
1. `POST /posts/{postId}/comments` - 发布评论（需要先设置当前用户）
2. `GET /comments/{commentId}/likes` - 获取新评论点赞信息
3. 后端通过 WebSocket 推送新评论和帖子评论数更新

### 9.6 点赞操作
1. `POST /posts/{postId}/like` 或 `POST /comments/{commentId}/like`
2. 后端通过 WebSocket 推送点赞数更新

### 9.7 切换角色
1. `POST /user/set-current` - 设置新的当前用户（会自动覆盖之前的用户）
2. 系统会自动为该用户创建AI用户（如果还没有的话）
3. 继续使用新角色的功能

**说明：**
- 无需先清除当前用户，直接设置新用户即可
- 系统会自动处理用户切换，同时只能有一个当前用户

---

## 10. 实现说明

### 10.1 时间处理
- 后端返回两个时间字段：
  - `timestamp`: 前端直接显示的格式化时间（如"刚刚"、"2分钟前"）
  - `createdAt`: ISO 8601 格式，用于前端排序和实时更新时间显示

### 10.2 点赞机制
- 每个帖子/评论只能点赞一次，不能取消
- 前端通过 `isLiked` 字段判断是否已点赞
- 已点赞的帖子/评论不响应再次点赞请求
- 点赞信息通过独立接口获取，便于缓存和异步更新

### 10.3 排序功能
- 评论支持按时间和按点赞数排序
- 前端通过 `sort` 参数指定排序方式
- 默认按时间排序（最新在上）

### 10.4 实时更新
- WebSocket 推送不定时的点赞和评论更新
- 前端需要根据推送消息更新对应的UI
- 推送消息包含完整的数据，前端直接替换即可

### 10.5 点赞接口解耦
- 内容获取接口不再返回点赞信息，减少数据传输量
- 点赞信息通过专门的接口获取，支持批量查询
- 前端分别调用内容接口和点赞接口，便于后续缓存优化
- 点赞操作接口仍返回最新点赞信息，用于即时反馈 
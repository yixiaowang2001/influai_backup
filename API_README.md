# InfluAI Backend API 使用指南

## 概述

这是一个基于FastAPI构建的InfluAI社交媒体模拟平台后端API。该API提供了完整的社交媒体功能，包括用户模板管理、帖子发布、评论系统、点赞功能以及实时更新。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python run_server.py
```

服务器将在 `http://localhost:8000` 启动。

### 3. 查看API文档

启动服务器后，可以访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. 运行测试

```bash
python test_api_flow.py
```

## API 接口说明

### 用户相关接口

#### 获取当前用户信息
- **GET** `/user/profile`
- 返回当前用户的基本信息

#### 获取用户模板列表
- **GET** `/user-templates`
- 返回所有可用的用户模板

#### 根据模板初始化AI用户
- **POST** `/user-templates/{template_name}/init-ai-users`
- 根据指定的用户模板初始化AI用户数据

### 帖子相关接口

#### 获取帖子列表
- **GET** `/posts`
- 返回最新的帖子列表（时间线）

#### 发布帖子
- **POST** `/posts`
- 发布新帖子
- 请求体: `{"content": "帖子内容"}`

#### 点赞帖子
- **POST** `/posts/{post_id}/like`
- 为指定帖子点赞

### 评论相关接口

#### 获取帖子评论
- **GET** `/posts/{post_id}/comments?sort=time`
- 获取指定帖子的评论列表
- 支持按时间(`time`)或点赞数(`likes`)排序

#### 发布评论
- **POST** `/posts/{post_id}/comments`
- 为指定帖子发布评论
- 请求体: `{"content": "评论内容"}`

#### 点赞评论
- **POST** `/comments/{comment_id}/like`
- 为指定评论点赞

### WebSocket 实时更新

#### WebSocket连接
- **WebSocket** `/ws/updates`
- 建立WebSocket连接接收实时更新

#### 推送消息类型
- `post_like_update`: 帖子点赞数更新
- `new_comment`: 新评论推送
- `comment_like_update`: 评论点赞数更新
- `new_post`: 新帖子推送

## 完整使用流程

### 1. 初始化阶段
1. 启动服务器
2. 获取用户模板列表
3. 选择模板初始化AI用户

### 2. 内容创建阶段
1. 发布帖子
2. 查看帖子列表
3. 为帖子点赞

### 3. 互动阶段
1. 查看帖子评论
2. 发布评论
3. 为评论点赞

### 4. 实时更新
1. 建立WebSocket连接
2. 接收实时推送消息
3. 更新前端界面

## 数据模型

### 用户模型
```json
{
  "id": "string",
  "username": "string",
  "userId": "string",
  "template": "string"
}
```

### 帖子模型
```json
{
  "id": "string",
  "content": "string",
  "author": "User",
  "timestamp": "string",
  "createdAt": "string",
  "likes": "number",
  "commentsCount": "number",
  "isLiked": "boolean"
}
```

### 评论模型
```json
{
  "id": "string",
  "content": "string",
  "author": "User",
  "timestamp": "string",
  "createdAt": "string",
  "likes": "number",
  "isLiked": "boolean"
}
```

## 响应格式

所有API接口都使用统一的响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 错误处理

API使用标准的HTTP状态码：
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 开发说明

### 项目结构
```
backend/
├── main.py              # FastAPI主应用
├── database/            # 数据库相关
│   ├── models.py        # 数据模型
│   ├── crud.py          # 数据库操作
│   └── init_db.py       # 数据库初始化
├── ai_module/           # AI相关模块
├── configs/             # 配置文件
├── data/                # 数据文件
├── services/            # 业务逻辑
└── utils/               # 工具函数
```

### 扩展开发

1. **添加新的API接口**：在 `main.py` 中添加新的路由
2. **修改数据模型**：更新 `database/models.py`
3. **添加业务逻辑**：在 `services/` 目录下创建新的服务模块
4. **配置管理**：在 `configs/` 目录下添加新的配置文件

### 数据库操作

- 使用SQLAlchemy ORM进行数据库操作
- 所有数据库操作都在 `database/crud.py` 中定义
- 数据库初始化在 `database/init_db.py` 中处理

## 注意事项

1. **字符限制**：帖子和评论内容限制为140字符
2. **点赞机制**：每个帖子/评论只能点赞一次
3. **实时更新**：通过WebSocket实现实时推送
4. **时间格式**：使用ISO 8601格式存储时间，前端显示相对时间

## 故障排除

### 常见问题

1. **服务器启动失败**
   - 检查端口8000是否被占用
   - 确认所有依赖已正确安装

2. **数据库连接失败**
   - 检查数据库文件权限
   - 确认SQLite数据库路径正确

3. **API请求失败**
   - 检查请求格式是否正确
   - 确认服务器正在运行

### 日志查看

服务器日志会输出到控制台和 `backend_debug.log` 文件中。

## 联系支持

如有问题，请查看API文档或检查服务器日志获取详细信息。 
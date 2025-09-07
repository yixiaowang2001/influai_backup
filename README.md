# InfluAI - AI驱动的社交媒体模拟平台

## 项目简介

InfluAI是一个基于人工智能的社交媒体模拟平台，能够模拟真实社交媒体的互动体验。通过预设的用户人设模板，AI会自动生成符合人设特点的评论，为用户提供沉浸式的社交媒体体验。

## 核心功能

### 🤖 AI评论生成
- 基于用户人设模板和帖子内容，使用大语言模型生成符合人设的评论
- 支持多种评论者态度分布（极差、不友善、中立、友善、极好、狂热）
- 智能预测帖子的点赞数、评论数和新增粉丝数

### 👥 用户模板系统
- **明星模板**：全能型娱乐明星，拥有百万级粉丝，风格前卫中性
- **网红模板**：美妆测评专家，专业实用，定期承接品牌合作
- **主播模板**：犀利段子手，擅长情绪输出和社会讽刺

### 🔄 实时互动体验
- WebSocket实时推送AI生成的评论
- 模拟真实社交媒体的评论节奏（每3-5秒推送一条）
- 支持点赞、评论等互动功能

### 📱 现代化界面
- 响应式设计，支持移动端和桌面端
- 简洁优雅的UI界面
- 实时更新，无需刷新页面

## 技术架构

### 后端技术栈
- **FastAPI**: 高性能Python Web框架
- **SQLAlchemy**: Python ORM，支持MySQL数据库
- **WebSocket**: 实时双向通信
- **OpenAI API**: 大语言模型集成
- **Uvicorn**: ASGI服务器

### 前端技术栈
- **原生HTML/CSS/JavaScript**: 轻量级前端实现
- **Tailwind CSS**: 现代化CSS框架
- **WebSocket API**: 实时通信

### 数据库设计
- **用户管理**: 人类用户和AI用户分离设计
- **内容管理**: 帖子、评论、点赞等完整社交功能
- **模板系统**: 可扩展的用户人设模板

## 快速开始

### 环境要求
- Python 3.8+
- MySQL 5.7+
- OpenAI API Key

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd influai_backup
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置数据库**
```bash
# 创建MySQL数据库
mysql -u root -p
CREATE DATABASE influai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. **配置API密钥**
在`backend/configs/`目录下创建`credential.py`文件：
```python
OPENAI_API_KEY = "your-openai-api-key"
```

5. **启动服务**
```bash
python run_server.py
```

6. **访问应用**
- 后端API: http://localhost:8000
- 前端界面: http://localhost:8000/frontend-web/
- API文档: http://localhost:8000/docs

## 使用指南

### 1. 创建用户
```bash
# 通过API创建人类用户
curl -X POST "http://localhost:8000/user/create" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "测试用户",
    "user_template_id": 1,
    "avatar_path": ""
  }'
```

### 2. 设置当前用户
```bash
# 设置当前用户（会创建对应的AI用户）
curl -X POST "http://localhost:8000/user/set-current" \
  -H "Content-Type: application/json" \
  -d '{"human_user_id": 1}'
```

### 3. 发布帖子
```bash
# 发布新帖子
curl -X POST "http://localhost:8000/posts" \
  -H "Content-Type: application/json" \
  -d '{"content": "这是一条测试帖子！"}'
```

### 4. 实时接收评论
通过WebSocket连接接收AI生成的评论：
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'new_comment_push') {
        console.log('收到AI评论:', data.data.comment);
    }
};
```

## API接口

### 用户管理
- `GET /user/profile` - 获取所有用户
- `POST /user/create` - 创建用户
- `POST /user/set-current` - 设置当前用户

### 帖子管理
- `GET /posts` - 获取帖子列表
- `POST /posts` - 发布帖子
- `POST /posts/{id}/like` - 点赞帖子

### 评论管理
- `GET /posts/{id}/comments` - 获取评论列表
- `POST /posts/{id}/comments` - 发布评论
- `POST /comments/{id}/like` - 点赞评论

### 系统状态
- `GET /system/status` - 系统状态
- `GET /health` - 健康检查
- `WebSocket /ws/updates` - 实时推送

## 项目结构

```
influai_backup/
├── backend/                 # 后端代码
│   ├── ai_module/          # AI模块
│   │   ├── llm.py          # LLM接口
│   │   ├── post_related.py # 帖子相关AI功能
│   │   └── prompts.py      # 提示词模板
│   ├── configs/            # 配置文件
│   ├── database/           # 数据库相关
│   ├── models/             # 数据模型
│   ├── services/           # 业务服务
│   └── utils/              # 工具函数
├── frontend-web/           # 前端代码
│   ├── index.html          # 主页面
│   └── main.js            # 前端逻辑
├── requirements.txt        # Python依赖
└── run_server.py          # 启动脚本
```

## 开发计划

### 已完成功能
- ✅ AI评论生成系统
- ✅ 用户模板管理
- ✅ WebSocket实时推送
- ✅ 基础社交功能（点赞、评论）
- ✅ 响应式前端界面

### 计划功能
- 🔄 推送通知系统
- 🔄 云端部署支持
- 🔄 异步评论生成优化
- 🔄 二级评论功能
- 🔄 用户删除接口

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至项目维护者

---

**InfluAI** - 让AI为你创造真实的社交媒体体验 🚀
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta

from backend.database.database import get_db
from backend.database import crud, models
from backend.database.init_db import init_database
from backend.utils.logger import get_logger
from backend.utils.global_utils import distribute_by_ratio

# 创建FastAPI应用
app = FastAPI(
    title="InfluAI Backend API",
    description="InfluAI社交媒体模拟平台后端API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 如果连接断开，从列表中移除
                self.active_connections.remove(connection)

manager = ConnectionManager()

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    logger.info("正在初始化数据库...")
    try:
        # 初始化数据库表结构和用户模板
        init_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

# 通用响应格式
def create_response(code: int = 200, message: str = "success", data: Any = None):
    return {
        "code": code,
        "message": message,
        "data": data
    }

# 时间格式化函数
def format_timestamp(created_at: datetime) -> str:
    """将datetime对象格式化为相对时间字符串"""
    now = datetime.now()
    diff = now - created_at
    
    if diff.total_seconds() < 60:
        return "刚刚"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes}分钟前"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours}小时前"
    else:
        days = int(diff.total_seconds() // 86400)
        return f"{days}天前"

# 用户相关接口
@app.get("/user/profile")
async def get_user_profile(db: Session = Depends(get_db)):
    """获取当前用户信息"""
    try:
        # 这里简化处理，返回默认用户信息
        # 在实际应用中，应该从认证系统获取用户信息
        user_data = {
            "id": "user_12345",
            "username": "默认用户",
            "userId": "@example_user",
            "template": "用户模版内容"
        }
        return create_response(data=user_data)
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")

# 用户模板相关接口
@app.get("/user-templates")
async def get_user_templates(db: Session = Depends(get_db)):
    """获取所有用户模板"""
    try:
        templates = crud.get_all_user_templates(db)
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.template_id,
                "name": template.template_name,
                "persona": template.persona,
                "follower_count": template.follower_count,
                "commenter_distribution": template.commenter_distribution,
                "default_avatar_path": template.default_avatar_path
            })
        return create_response(data=template_list)
    except Exception as e:
        logger.error(f"获取用户模板失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户模板失败")

@app.post("/user-templates/{template_name}/init-ai-users")
async def init_ai_users_by_template(template_name: str, db: Session = Depends(get_db)):
    """根据用户模板初始化AI用户"""
    try:
        template = crud.get_user_template_by_name(db, template_name)
        if not template:
            raise HTTPException(status_code=404, detail=f"未找到模板: {template_name}")
        
        # 检查是否已经有AI用户
        existing_users = crud.get_all_ai_users(db)
        if existing_users:
            return create_response(message="AI用户已存在，跳过初始化")
        
        # 初始化AI用户
        from backend.database.init_db import insert_init_data
        insert_init_data(template_name)
        
        return create_response(message=f"成功根据模板 '{template_name}' 初始化AI用户")
    except Exception as e:
        logger.error(f"初始化AI用户失败: {e}")
        raise HTTPException(status_code=500, detail="初始化AI用户失败")

# 帖子相关接口
@app.get("/posts")
async def get_posts(db: Session = Depends(get_db)):
    """获取帖子列表（时间线）"""
    try:
        posts = crud.get_latest_n_posts(db, 50)  # 获取最新50条帖子
        post_list = []
        
        for post in posts:
            post_data = {
                "id": f"post_{post.post_id}",
                "content": post.post_content,
                "author": {
                    "id": "user_12345",
                    "username": "默认用户",
                    "userId": "@example_user"
                },
                "timestamp": format_timestamp(post.created_at),
                "createdAt": post.created_at.isoformat(),
                "likes": post.like_count,
                "commentsCount": len(post.comments),
                "isLiked": False  # 简化处理，实际应该根据当前用户判断
            }
            post_list.append(post_data)
        
        return create_response(data=post_list)
    except Exception as e:
        logger.error(f"获取帖子列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取帖子列表失败")

@app.post("/posts")
async def create_post(post_data: Dict[str, str], db: Session = Depends(get_db)):
    """发布帖子"""
    try:
        content = post_data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="帖子内容不能为空")
        
        if len(content) > 140:
            raise HTTPException(status_code=400, detail="帖子内容不能超过140字符")
        
        # 创建帖子
        new_post = models.Post(
            post_content=content,
            like_count=0,
            created_at=datetime.now()
        )
        
        created_post = crud.create_post(db, new_post)
        
        # 返回创建的帖子数据
        post_response = {
            "id": f"post_{created_post.post_id}",
            "content": created_post.post_content,
            "author": {
                "id": "user_12345",
                "username": "默认用户",
                "userId": "@example_user"
            },
            "timestamp": format_timestamp(created_post.created_at),
            "createdAt": created_post.created_at.isoformat(),
            "likes": created_post.like_count,
            "commentsCount": 0,
            "isLiked": False
        }
        
        # 通过WebSocket广播新帖子
        await manager.broadcast(json.dumps({
            "type": "new_post",
            "data": post_response
        }))
        
        return create_response(data=post_response)
    except Exception as e:
        logger.error(f"发布帖子失败: {e}")
        raise HTTPException(status_code=500, detail="发布帖子失败")

@app.post("/posts/{post_id}/like")
async def like_post(post_id: str, db: Session = Depends(get_db)):
    """点赞帖子"""
    try:
        # 从post_id中提取数字ID
        try:
            numeric_id = int(post_id.replace("post_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的帖子ID")
        
        # 获取帖子
        post = db.query(models.Post).filter(models.Post.post_id == numeric_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 增加点赞数
        post.like_count += 1
        db.commit()
        
        # 通过WebSocket广播点赞更新
        await manager.broadcast(json.dumps({
            "type": "post_like_update",
            "data": {
                "postId": post_id,
                "likes": post.like_count
            }
        }))
        
        return create_response(data={
            "postId": post_id,
            "likes": post.like_count
        })
    except Exception as e:
        logger.error(f"点赞帖子失败: {e}")
        raise HTTPException(status_code=500, detail="点赞帖子失败")

# 评论相关接口
@app.get("/posts/{post_id}/comments")
async def get_comments(post_id: str, sort: str = "time", db: Session = Depends(get_db)):
    """获取帖子评论列表"""
    try:
        # 从post_id中提取数字ID
        try:
            numeric_id = int(post_id.replace("post_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的帖子ID")
        
        comments = crud.get_comments_by_post(db, numeric_id)
        
        # 根据排序方式排序
        if sort == "likes":
            comments = sorted(comments, key=lambda x: x.comment_likes, reverse=True)
        else:  # 默认按时间排序
            comments = sorted(comments, key=lambda x: x.created_at, reverse=True)
        
        comment_list = []
        for comment in comments:
            # 获取AI用户信息
            ai_user = None
            if comment.ai_user_id:
                ai_user = crud.get_ai_user(db, comment.ai_user_id)
            
            comment_data = {
                "id": f"comment_{comment.comment_id}",
                "content": comment.comment_content,
                "author": {
                    "id": ai_user.user_id if ai_user else "unknown",
                    "username": ai_user.username if ai_user else "未知用户",
                    "userId": f"@{ai_user.username.lower()}" if ai_user else "@unknown"
                },
                "timestamp": format_timestamp(comment.created_at),
                "createdAt": comment.created_at.isoformat(),
                "likes": comment.comment_likes,
                "isLiked": False
            }
            comment_list.append(comment_data)
        
        return create_response(data=comment_list)
    except Exception as e:
        logger.error(f"获取评论列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取评论列表失败")

@app.post("/posts/{post_id}/comments")
async def create_comment(post_id: str, comment_data: Dict[str, str], db: Session = Depends(get_db)):
    """发布评论"""
    try:
        # 从post_id中提取数字ID
        try:
            numeric_id = int(post_id.replace("post_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的帖子ID")
        
        content = comment_data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="评论内容不能为空")
        
        if len(content) > 140:
            raise HTTPException(status_code=400, detail="评论内容不能超过140字符")
        
        # 检查帖子是否存在
        post = db.query(models.Post).filter(models.Post.post_id == numeric_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 创建评论（这里简化处理，实际应该根据AI用户生成评论）
        # 直接创建Comment对象并添加到数据库
        new_comment = models.Comment(
            comment_content=content,
            comment_user_type=1,  # 简化处理
            comment_level=1,
            comment_likes=0,
            master_comment_id=None,
            created_at=datetime.now(),
            send_at=datetime.now(),
            post_id=numeric_id,
            ai_user_id=None  # 简化处理，实际应该分配AI用户
        )
        
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        created_comment = new_comment
        
        # 返回创建的评论数据
        comment_response = {
            "id": f"comment_{created_comment.comment_id}",
            "content": created_comment.comment_content,
            "author": {
                "id": "user_12345",
                "username": "默认用户",
                "userId": "@example_user"
            },
            "timestamp": format_timestamp(created_comment.created_at),
            "createdAt": created_comment.created_at.isoformat(),
            "likes": created_comment.comment_likes,
            "isLiked": False
        }
        
        # 通过WebSocket广播新评论
        await manager.broadcast(json.dumps({
            "type": "new_comment",
            "data": {
                "postId": post_id,
                "comment": comment_response,
                "commentsCount": len(post.comments) + 1
            }
        }))
        
        return create_response(data=comment_response)
    except Exception as e:
        logger.error(f"发布评论失败: {e}")
        raise HTTPException(status_code=500, detail="发布评论失败")

@app.post("/comments/{comment_id}/like")
async def like_comment(comment_id: str, db: Session = Depends(get_db)):
    """点赞评论"""
    try:
        # 从comment_id中提取数字ID
        try:
            numeric_id = int(comment_id.replace("comment_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的评论ID")
        
        # 获取评论
        comment = db.query(models.Comment).filter(models.Comment.comment_id == numeric_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 增加点赞数
        comment.comment_likes += 1
        db.commit()
        
        # 通过WebSocket广播点赞更新
        await manager.broadcast(json.dumps({
            "type": "comment_like_update",
            "data": {
                "commentId": comment_id,
                "postId": f"post_{comment.post_id}",
                "likes": comment.comment_likes
            }
        }))
        
        return create_response(data={
            "commentId": comment_id,
            "likes": comment.comment_likes
        })
    except Exception as e:
        logger.error(f"点赞评论失败: {e}")
        raise HTTPException(status_code=500, detail="点赞评论失败")

# WebSocket接口
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            # 这里可以处理客户端发送的消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return create_response(message="服务运行正常")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
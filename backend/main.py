from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from backend.database.database import get_db
from backend.database import crud, models
from backend.database.init_db import init_database
from backend.utils.logger import get_logger
from backend.utils.global_utils import distribute_by_ratio

# Pydantic模型定义
class SetCurrentUserRequest(BaseModel):
    """设置当前用户的请求模型"""
    human_user_id: int = Field(
        ..., 
        description="人类用户ID，用于设置当前全局用户", 
        example=1,
        gt=0
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "human_user_id": 1
            }
        }
    }

class CreatePostRequest(BaseModel):
    """创建帖子的请求模型"""
    content: str = Field(
        ..., 
        description="帖子内容，不能为空且不能超过140字符", 
        example="这是一条测试帖子！今天天气真不错！",
        min_length=1,
        max_length=140
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "这是一条测试帖子！今天天气真不错！"
            }
        }
    }

class CreateCommentRequest(BaseModel):
    """创建评论的请求模型"""
    content: str = Field(
        ..., 
        description="评论内容，不能为空且不能超过140字符", 
        example="这是一条测试评论！说得很有道理！",
        min_length=1,
        max_length=140
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "这是一条测试评论！说得很有道理！"
            }
        }
    }

# 创建FastAPI应用
app = FastAPI(
    title="InfluAI Backend API",
    description="""
    InfluAI社交媒体模拟平台后端API
    
    ## 功能特性
    
    * **用户管理** - 支持人类用户和AI用户管理
    * **帖子系统** - 发布、点赞、评论功能
    * **实时更新** - WebSocket实时推送更新
    * **AI评论** - 基于用户模板自动生成AI评论
    
    ## 快速开始
    
    1. 设置当前用户: `POST /user/set-current`
    2. 发布帖子: `POST /posts`
    3. 查看帖子: `GET /posts`
    4. 点赞评论: `POST /posts/{post_id}/like`
    
    ## WebSocket
    
    连接 `ws://localhost:8000/ws/updates` 获取实时更新
    """,
    version="1.0.0",
    contact={
        "name": "InfluAI Team",
        "email": "support@influai.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# 全局用户管理
class GlobalUserManager:
    def __init__(self):
        self.current_human_user = None
    
    def set_current_user(self, human_user):
        """设置当前用户（会覆盖之前的用户）"""
        self.current_human_user = human_user
        logger.info(f"设置当前用户: {human_user.username} (ID: {human_user.user_id})")
    
    def get_current_user(self):
        """获取当前用户"""
        return self.current_human_user

# 全局用户管理器实例
user_manager = GlobalUserManager()

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
    """应用启动时的初始化操作"""
    try:
        logger.info("InfluAI Backend API 启动中...")
        
        # 初始化数据库（如果还没有初始化）
        from backend.database.init_db import init_database
        if init_database():
            logger.info("数据库初始化完成")
        else:
            logger.warning("数据库初始化失败，但应用继续启动")
        
        logger.info("InfluAI Backend API 启动完成")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
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


async def generate_comments_for_post(post_id: int, human_user_id: int, db: Session):
    """为帖子生成评论"""
    try:
        logger.info(f"开始为帖子 {post_id} 生成评论，人类用户ID: {human_user_id}...")
        
        # 获取人类用户信息
        human_user = crud.get_human_user_by_id(db, human_user_id)
        if not human_user:
            logger.error(f"未找到人类用户ID: {human_user_id}")
            return
        
        # 获取用户模板
        template = crud.get_user_template_by_id(db, human_user.user_template_id)
        if not template:
            logger.error(f"未找到模板ID: {human_user.user_template_id}")
            return
        
        # 获取帖子内容
        post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
        if not post:
            logger.error(f"未找到帖子ID: {post_id}")
            return
        
        # 获取该人类用户的所有AI用户
        ai_users = crud.get_ai_users_by_human_user_id(db, human_user_id)
        if not ai_users:
            logger.warning(f"人类用户 {human_user_id} 没有对应的AI用户")
            return
        
        # 使用PostService生成评论
        from backend.services.post_service import PostService
        from backend.models import Post as PostModel, Comment as CommentModel
        
        # 创建Post对象用于PostService
        post_for_service = PostModel(
            post_content=post.post_content,
            like_count=post.like_count,
            created_at=post.created_at
        )
        
        # 初始化PostService
        post_service = PostService(
            content=post.post_content,
            template_id=template.template_id,
            human_user_id=human_user_id,
            db=db
        )
        
        # 运行PostService生成评论
        stats = post_service.generate_comments_for_existing_post(post_id)
        
        # 更新帖子的统计数据
        post.like_count = stats["pred_like_count"]
        db.commit()
        
        logger.info(f"帖子 {post_id} 的评论生成完成，共 {len(post_service.comments)} 条")
        
        # 通过WebSocket广播评论数更新
        await manager.broadcast(json.dumps({
            "type": "post_comments_update",
            "data": {
                "postId": f"post_{post_id}",
                "commentsCount": len(post_service.comments),
                "likes": post.like_count
            }
        }))
        
    except Exception as e:
        logger.error(f"生成评论失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

# 用户相关接口
@app.get("/user/profile")
async def get_all_human_users(db: Session = Depends(get_db)):
    """获取所有人类用户信息"""
    try:
        human_users = crud.get_all_human_users(db)
        
        user_list = []
        for human_user in human_users:
            user_data = {
                "humanUserId": human_user.user_id,
                "humanUsername": human_user.username,
                "avatarPath": human_user.avatar_path,
                "followerCount": human_user.follower_count,
                "userTemplateId": human_user.user_template_id,
                "createdAt": human_user.created_at.isoformat()
            }
            user_list.append(user_data)
        
        return create_response(data=user_list)
    except Exception as e:
        logger.error(f"获取所有人类用户信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取所有人类用户信息失败")


@app.get("/user/profile/{human_user_id}")
async def get_human_user_by_id(human_user_id: int, db: Session = Depends(get_db)):
    """获取特定人类用户信息"""
    try:
        human_user = crud.get_human_user_by_id(db, human_user_id)
        
        if not human_user:
            raise HTTPException(status_code=404, detail=f"未找到用户ID为 {human_user_id} 的用户")
        
        user_data = {
            "humanUserId": human_user.user_id,
            "humanUsername": human_user.username,
            "avatarPath": human_user.avatar_path,
            "followerCount": human_user.follower_count,
            "userTemplateId": human_user.user_template_id,
            "createdAt": human_user.created_at.isoformat()
        }
        return create_response(data=user_data)
    except HTTPException:
        # 重新抛出HTTPException，避免被通用异常处理捕获
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


@app.get("/user/current")
async def get_current_user():
    """获取当前用户信息"""
    try:
        current_user = user_manager.get_current_user()
        if not current_user:
            raise HTTPException(status_code=404, detail="未设置当前用户")
        
        user_data = {
            "humanUserId": current_user.user_id,
            "humanUsername": current_user.username,
            "avatarPath": current_user.avatar_path,
            "followerCount": current_user.follower_count,
            "userTemplateId": current_user.user_template_id,
            "createdAt": current_user.created_at.isoformat()
        }
        return create_response(data=user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取当前用户信息失败")


# 用户模板相关接口
@app.get("/user-templates",
         summary="获取用户模板列表",
         description="获取所有可用的用户模板，包含模板ID、名称、人设描述、粉丝数等信息。",
         response_description="返回用户模板列表")
async def get_user_templates(db: Session = Depends(get_db)):
    """获取用户模板列表"""
    try:
        templates = crud.get_all_user_templates(db)
        template_list = []
        for template in templates:
            template_data = {
                "id": template.template_id,
                "name": template.template_name,
                "persona": template.persona,
                "follower_count": template.follower_count,
                "commenter_distribution": template.commenter_distribution,
                "default_avatar_path": template.default_avatar_path
            }
            template_list.append(template_data)
        
        return create_response(data=template_list)
    except Exception as e:
        logger.error(f"获取用户模板失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户模板失败")


@app.post("/user/set-current", 
          summary="设置当前用户",
          description="通过用户ID设置当前全局用户，用于后续的帖子发布等操作。同时只能有一个当前用户，设置新用户会覆盖之前的用户。如果该用户没有对应的AI用户，会自动根据用户模板创建AI用户。",
          response_description="设置成功返回用户信息")
async def set_current_user(user_data: SetCurrentUserRequest, db: Session = Depends(get_db)):
    """设置当前用户（通过human_user_id设置）"""
    try:
        human_user_id = user_data.human_user_id
        
        # 查找人类用户
        human_user = crud.get_human_user_by_id(db, human_user_id)
        if not human_user:
            raise HTTPException(status_code=404, detail=f"未找到用户ID: {human_user_id}")
        
        # 检查该用户是否已有对应的AI用户
        existing_ai_users = crud.get_ai_users_by_human_user_id(db, human_user_id)
        
        # 如果没有AI用户，则根据用户模板创建AI用户
        if not existing_ai_users:
            # 获取用户模板
            template = crud.get_user_template_by_id(db, human_user.user_template_id)
            if template:
                # 将数据库对象转换为字典格式
                user_template_dict = {
                    "persona": template.persona,
                    "follower_count": template.follower_count,
                    "commenter_distribution": template.commenter_distribution,
                    "default_avatar_path": template.default_avatar_path
                }
                
                # 初始化AI用户
                from backend.database.db_utils import init_ai_users
                all_ai_users = init_ai_users(user_template_dict, human_user_id)
                
                for ai_user in all_ai_users:
                    db.add(ai_user)
                db.commit()
                
                logger.info(f"为人类用户 {human_user.username} (ID: {human_user_id}) 成功创建 {len(all_ai_users)} 个AI用户")
            else:
                logger.warning(f"未找到用户模板ID: {human_user.user_template_id}")
        
        # 设置为当前用户（会覆盖之前的用户）
        user_manager.set_current_user(human_user)
        
        return create_response(data={
            "humanUserId": human_user.user_id,
            "humanUsername": human_user.username,
            "userTemplateId": human_user.user_template_id,
            "message": "当前用户设置成功" + (f"，已创建 {len(existing_ai_users) if existing_ai_users else len(all_ai_users)} 个AI用户" if not existing_ai_users else "")
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置当前用户失败: {e}")
        raise HTTPException(status_code=500, detail="设置当前用户失败")




# 帖子相关接口
@app.get("/posts",
         summary="获取帖子列表",
         description="获取最新的帖子列表（时间线），返回最新的50条帖子。",
         response_description="返回帖子列表，包含作者信息、点赞数、评论数等")
async def get_posts(db: Session = Depends(get_db)):
    """获取帖子列表（时间线）"""
    try:
        posts = crud.get_latest_n_posts(db, 50)  # 获取最新50条帖子
        post_list = []
        
        for post in posts:
            # 获取作者信息
            author = crud.get_human_user_by_id(db, post.author_id) if post.author_id else None
            
            post_data = {
                "id": f"post_{post.post_id}",
                "content": post.post_content,
                "author": {
                    "id": f"user_{author.user_id}" if author else "unknown",
                    "username": author.username if author else "未知用户",
                    "userId": f"@{author.username.lower()}" if author else "@unknown"
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

@app.post("/posts",
          summary="发布帖子",
          description="发布新帖子。需要先设置当前用户，帖子内容不能超过140字符。发布后会自动根据用户模板生成AI评论。",
          response_description="发布成功返回帖子详细信息")
async def create_post(post_data: CreatePostRequest, db: Session = Depends(get_db)):
    """发布帖子"""
    try:
        content = post_data.content
        
        # 获取当前用户
        current_user = user_manager.get_current_user()
        if not current_user:
            raise HTTPException(status_code=400, detail="请先设置当前用户")
        
        # 创建帖子
        new_post = models.Post(
            post_content=content,
            author_id=current_user.user_id,
            like_count=0,
            created_at=datetime.now()
        )
        
        created_post = crud.create_post(db, new_post)
        
        # 获取作者信息用于响应
        author = crud.get_human_user_by_id(db, current_user.user_id)
        
        # 返回创建的帖子数据
        post_response = {
            "id": f"post_{created_post.post_id}",
            "content": created_post.post_content,
            "author": {
                "id": f"user_{author.user_id}",
                "username": author.username,
                "userId": f"@{author.username.lower()}"
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
        
        # 同步生成评论（便于调试）
        try:
            await generate_comments_for_post(created_post.post_id, current_user.user_id, db)
        except Exception as e:
            logger.error(f"生成评论时出错: {e}")
            # 不阻塞帖子发布，继续返回响应
        
        return create_response(data=post_response)
    except HTTPException:
        # 重新抛出HTTPException，避免被通用异常处理捕获
        raise
    except Exception as e:
        logger.error(f"发布帖子失败: {e}")
        raise HTTPException(status_code=500, detail="发布帖子失败")

@app.post("/posts/{post_id}/like",
          summary="点赞帖子",
          description="为指定帖子点赞，增加帖子的点赞数。",
          response_description="点赞成功返回更新后的点赞数")
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
@app.get("/posts/{post_id}/comments",
         summary="获取帖子评论",
         description="获取指定帖子的评论列表。支持按时间或点赞数排序。",
         response_description="返回评论列表，包含评论者信息、点赞数等")
async def get_comments(
    post_id: str, 
    sort: str = "time", 
    db: Session = Depends(get_db)
):
    """
    获取帖子评论列表
    
    Args:
        post_id: 帖子ID，格式为 "post_数字"
        sort: 排序方式，"time" 按时间排序，"likes" 按点赞数排序
        db: 数据库会话
    """
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
            # 根据sender_type获取用户信息
            author_info = {}
            if comment.sender_type == "ai_user":
                # 获取AI用户信息
                ai_user = crud.get_ai_user(db, comment.sender_id)
                if ai_user:
                    author_info = {
                        "id": ai_user.user_id,
                        "username": ai_user.username,
                        "userId": f"@{ai_user.username.lower()}"
                    }
                else:
                    author_info = {
                        "id": "unknown",
                        "username": "未知AI用户",
                        "userId": "@unknown"
                    }
            elif comment.sender_type == "human_user":
                # 获取人类用户信息
                human_user = crud.get_human_user_by_id(db, int(comment.sender_id))
                if human_user:
                    author_info = {
                        "id": f"human_{human_user.user_id}",
                        "username": human_user.username,
                        "userId": f"@{human_user.username.lower()}"
                    }
                else:
                    author_info = {
                        "id": "unknown",
                        "username": "未知用户",
                        "userId": "@unknown"
                    }
            else:
                author_info = {
                    "id": "unknown",
                    "username": "未知用户",
                    "userId": "@unknown"
                }
            
            comment_data = {
                "id": f"comment_{comment.comment_id}",
                "content": comment.comment_content,
                "author": author_info,
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

@app.post("/posts/{post_id}/comments",
          summary="发布评论",
          description="为指定帖子发布评论。评论内容不能超过140字符。当前用户必须是已设置的人类用户。",
          response_description="发布成功返回评论详细信息")
async def create_comment(post_id: str, comment_data: CreateCommentRequest, db: Session = Depends(get_db)):
    """发布评论"""
    try:
        # 检查当前用户是否已设置
        current_user = user_manager.get_current_user()
        if not current_user:
            raise HTTPException(status_code=400, detail="请先设置当前用户")
        
        # 从post_id中提取数字ID
        try:
            numeric_id = int(post_id.replace("post_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的帖子ID")
        
        content = comment_data.content
        
        # 检查帖子是否存在
        post = db.query(models.Post).filter(models.Post.post_id == numeric_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 创建评论（当前用户发布）
        new_comment = crud.create_comment_with_sender(
            db=db,
            comment_content=content,
            post_id=numeric_id,
            sender_id=str(current_user.user_id),
            sender_type="human_user",
            comment_user_type=1,
            comment_level=1
        )
        
        # 返回创建的评论数据
        comment_response = {
            "id": f"comment_{new_comment.comment_id}",
            "content": new_comment.comment_content,
            "author": {
                "id": f"human_{current_user.user_id}",
                "username": current_user.username,
                "userId": f"@{current_user.username.lower()}"
            },
            "timestamp": format_timestamp(new_comment.created_at),
            "createdAt": new_comment.created_at.isoformat(),
            "likes": new_comment.comment_likes,
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

@app.post("/comments/{comment_id}/like",
          summary="点赞评论",
          description="为指定评论点赞，增加评论的点赞数。",
          response_description="点赞成功返回更新后的点赞数")
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
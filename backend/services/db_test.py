"""
数据库测试文件
用于测试数据库操作功能
"""
from backend.database.crud import (
    create_post,
    create_comment,
    create_ai_user,
    get_latest_n_posts,
    get_comments_by_post
)
from backend.database.database import get_db_session
from backend.database.init_db import init_database
from backend.models import (
    Post,
    Comment,
    AIUser,
    Attitude
)

# 初始化数据库
init_database()

# 获取数据库会话
db = get_db_session()

# 测试创建帖子
# new_post = Post(
#     post_content="今天天气真好！"
# )
#
# create_post = create_post(db, new_post)
#
# 测试创建评论
# new_comment = Comment(
#     comment_content="非常好！",
#     comment_user_type=0,
#     comment_attitude=Attitude.NEUTRAL,
#     comment_level=0,
#     comment_likes=0,
#     post_id=create_post.post_id
# )
#
# create_comment(db, new_comment)
#
# 测试创建AI用户
# new_ai_user = AIUser(
#     username="王一笑"
# )
#
# create_ai_user(db, new_ai_user)
# print(len(get_comments_by_post(db, 1)))

# 关闭数据库连接
db.close()

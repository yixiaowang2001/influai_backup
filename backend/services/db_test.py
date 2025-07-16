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

init_database()

db = get_db_session()

# new_post = Post(
#     post_content="今天天气真好！"
# )
#
# create_post = create_post(db, new_post)
#
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
# new_ai_user = AIUser(
#     username="王一笑"
# )
#
# create_ai_user(db, new_ai_user)
# print(len(get_comments_by_post(db, 1)))


db.close()

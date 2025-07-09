from backend.models import Post as PostModel
from backend.database.init_db import init_database
from backend.database.crud import *

db = init_database()

# 创建 dataclass 对象
new_post = PostModel(post_content="今天天气真好！")

# 保存到数据库
db_post = create_post(db, new_post)
print(f"创建的帖子ID: {db_post.post_id}")
import random
import string
from datetime import datetime
from backend.database import models


def init_ai_users(user_template: dict):
    """
    随机生成n个AI用户对象，不进行数据库操作，直接返回AIUser对象列表。

    :param user_template: 人类用户模版
    :return: AIUser对象列表
    """
    ai_users = []
    init_ai_user_num = int(user_template['follower_count']) * 2

    for _ in range(init_ai_user_num):
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        username = f"云粉爱_{rand_str}"
        ai_user = models.AIUser(
            username=username,
            avatar_path="/data/default_avatars/test.png",
            attitude_value=1,
        )
        ai_users.append(ai_user)

    return ai_users
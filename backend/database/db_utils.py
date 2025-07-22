import random
import string

from backend.database import models
from backend.models.attitude import Attitude
from backend.utils import distribute_by_ratio


def init_ai_users(user_template: dict):
    """
    随机生成n个AI用户对象，不进行数据库操作，直接返回AIUser对象列表。
    用户数量为人类用户粉丝数的两倍。
    一半用户为中立态度(attitude_value=0)，
    另一半根据commenter_distribution在不同态度范围内随机生成两位小数的attitude_value。

    :param user_template: 人类用户模版，包含follower_count和commenter_distribution
    :return: AIUser对象列表
    """
    ai_users = []
    init_ai_user_num = int(user_template['follower_count']) * 2
    
    # 一半用户为中立态度
    neutral_count = init_ai_user_num // 2
    # 另一半根据分布分配
    distributed_count = init_ai_user_num - neutral_count
    
    # 生成中立用户
    for _ in range(neutral_count):
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        username = f"云粉爱_{rand_str}"
        ai_user = models.AIUser(
            username=username,
            avatar_path="/data/default_avatars/test.png",
            attitude_value=0.0,
        )
        ai_users.append(ai_user)
    
    # 根据commenter_distribution生成有态度倾向的用户
    commenter_distribution = user_template['commenter_distribution']
    
    # 使用工具方法计算每种态度类型需要生成的用户数量
    attitude_counts = distribute_by_ratio(distributed_count, commenter_distribution)
    
    # 生成有态度倾向的用户
    for attitude_name, count in attitude_counts.items():
        if count <= 0:
            continue
            
        # 获取态度类型对应的数值范围
        attitude_enum = Attitude.parse(attitude_name)
        if attitude_enum:
            lower_bound, upper_bound = attitude_enum.value
            
            for _ in range(count):
                # 在范围内随机生成两位小数的attitude_value
                attitude_value = round(random.uniform(lower_bound, upper_bound), 2)
                
                rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                username = f"云粉爱_{rand_str}"
                ai_user = models.AIUser(
                    username=username,
                    avatar_path="/data/default_avatars/test.png",
                    attitude_value=attitude_value,
                )
                ai_users.append(ai_user)

    return ai_users



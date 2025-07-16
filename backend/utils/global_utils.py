import math
import random
from typing import List


def rand_int(
        number: float,
        float_range: float = 0.1,
) -> int:
    """
    生成指定范围内的随机整数
    
    Args:
        number: 基准数值
        float_range: 浮动范围比例
        
    Returns:
        int: 随机整数
    """
    low = number * (1 - float_range)
    high = number * (1 + float_range)

    low_bound = math.ceil(low)
    high_bound = math.floor(high)

    return random.randint(low_bound, high_bound)


def format_history_posts(posts: List, n: int) -> List[str]:
    """
    格式化历史帖子列表，返回前n个帖子的内容字符串列表
    
    Args:
        posts: 帖子对象列表
        n: 要返回的帖子数量
        
    Returns:
        List[str]: 前n个帖子的内容字符串列表
    """
    if not posts:
        return []

    recent_posts = posts[:n]

    formatted_posts = []
    for i, post in enumerate(recent_posts, 1):
        post_content = getattr(post, 'post_content', str(post))
        formatted_posts.append(f"{i}. {post_content}")

    return formatted_posts


if __name__ == '__main__':
    print(rand_int(10))

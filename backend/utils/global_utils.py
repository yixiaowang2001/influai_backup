import math
import random
from typing import List, Dict


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


def distribute_by_ratio(
        total: int,
        ratios: Dict[str, float]
) -> Dict[str, int]:
    """
    根据比例分布分配总数到各个类别
    
    Args:
        total: 需要分配的总数
        ratios: 各类别的比例字典，格式为 {"类别名": 比例值}
        
    Returns:
        Dict[str, int]: 各类别分配到的数量
    """
    total_ratio = sum(ratios.values())
    result = {}
    fractional_parts = []
    allocated = 0

    # 先按比例分配整数部分
    for key, ratio in ratios.items():
        exact_value = total * ratio / total_ratio
        integer_part = int(exact_value)
        result[key] = integer_part
        allocated += integer_part
        fractional_parts.append((exact_value - integer_part, key))

    # 处理剩余的小数部分，按小数部分大小排序分配
    remaining = total - allocated
    if remaining > 0:
        fractional_parts.sort(key=lambda x: x[0], reverse=True)
        for i in range(remaining):
            _, key = fractional_parts[i]
            result[key] += 1

    return result


if __name__ == '__main__':
    print(rand_int(10))

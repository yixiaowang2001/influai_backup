import math
import random


def rand_int(
        number: float,
        float_range: float = 0.1,
) -> int:
    low = number * (1 - float_range)
    high = number * (1 + float_range)

    low_bound = math.ceil(low)
    high_bound = math.floor(high)

    return random.randint(low_bound, high_bound)


def format_history_posts(posts: list, n: int) -> list[str]:
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

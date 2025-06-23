from prompts import get_generate_level1_comments_prompt
from llm import chat


def generate_level1_comments(
        persona: str,
        post_content: str,
        commenter_distribution: dict,
        each_type_n: int,
        history_posts: list = None,
):
    """
    基于以下信息，生成level1评论
    :param persona: 人类用户人设
    :param post_content: 帖子内容
    :param history_posts: 历史帖子
    :param commenter_distribution: 评论者分布
    :param each_type_n: 每个评论者类别生成的评论数量
    :return: 生成的所有评论
    """
    system_prompt, user_prompt = get_generate_level1_comments_prompt(
        persona=persona,
        post_content=post_content,
        commenter_distribution=commenter_distribution,
        each_type_n=each_type_n,
        history_posts=history_posts,
    )
    response = chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name="qwen-plus",
        temperature=1.99,
        max_tokens=4096
    )
    print(response)
    gen_l1_comments = []
    return gen_l1_comments


def generate_similar_level1_comments():
    pass


def generate_level2_comments():
    pass


def generate_similar_level2_comments():
    pass


if __name__ == '__main__':
    from backend.data.test_data import GAMER
    post_content = "上海人别他妈看我直播，都是傻逼"

    generate_level1_comments(
        persona=GAMER["persona"],
        post_content=post_content,
        commenter_distribution=GAMER["commenter_distribution"],
        each_type_n=5,
    )

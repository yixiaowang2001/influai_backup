from backend.models.enums import Attitude
from llm import chat
from llm_utils import parse_json_response
from prompts import get_predict_post_stats_prompt, get_update_commenter_distribution_prompt


def predict_post_stats(
        persona: str,
        follower_count: int,
        post_content: str,
        history_posts: list = None,
):
    """
    基于以下信息，预测用户当前的帖子会有多少转发、新增关注、评论、点赞数量。
    :param persona: 用户人设
    :param follower_count: 用户粉丝数量
    :param post_content: 帖子内容
    :param history_posts: 历史帖子内容
    :return: 预测新增关注量，预测评论量，预测点赞量
    """

    system_prompt, user_prompt = get_predict_post_stats_prompt(
        persona=persona,
        follower_count=follower_count,
        post_content=post_content,
        history_posts=history_posts,
    )

    response = chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name="qwen-turbo",
        temperature=0.1,
        max_tokens=256
    )

    default_response = {
        "pred_new_follower_count": 0,
        "pred_comment_count": 0,
        "pred_like_count": 0
    }

    return parse_json_response(response, default_response)


def update_commenter_distribution(
        prev_commenter_distribution: dict,
        persona: str,
        post_content: str,
        history_posts: list = None,
):
    """
    基于以下信息，更新人类用户评论者分布。
    :param prev_commenter_distribution: 旧评论者分布
    :param persona: 用户人设
    :param post_content: 帖子内容
    :param history_posts: 历史帖子内容
    :return: 新评论者分布
    """
    system_prompt, user_prompt = get_update_commenter_distribution_prompt(
        prev_commenter_distribution=prev_commenter_distribution,
        persona=persona,
        post_content=post_content,
        history_posts=history_posts,
    )

    response = chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name="qwen-turbo",
        temperature=0.1,
        max_tokens=256
    )

    default_response = {
        Attitude.BAD: 0.0,
        Attitude.NEUTRAL_NEGATIVE: 0.0,
        Attitude.NEUTRAL: 0.0,
        Attitude.NEUTRAL_POSITIVE: 0.0,
        Attitude.GOOD: 0.0,
        Attitude.PERFECT: 0.0
    }

    json_response = parse_json_response(response, default_response)
    json_converted = {}
    for key, value in json_response.items():
        enum_value = Attitude.from_label(key)
        if enum_value is None:
            return default_response
        json_converted[enum_value] = value
    return json_converted


if __name__ == '__main__':
    from backend.data.test_data import GAMER

    post_content = "上海人别他妈看我直播，都是傻逼"

    # print(predict_post_stats(
    #     persona=GAMER["persona"],
    #     follower_count=GAMER["follower_count"],
    #     post_content=post_content,
    # ))

    print(update_commenter_distribution(
        prev_commenter_distribution=GAMER["commenter_distribution"],
        persona=GAMER["persona"],
        post_content=post_content,
    ))

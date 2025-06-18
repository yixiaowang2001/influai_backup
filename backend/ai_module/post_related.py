from inference import chat
from prompts import get_predict_post_stats_prompt

import re
import json


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
    :return: 预测转发量，预测新增关注量，预测评论量，预测点赞量
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

    print(response)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    cleaned_response = response.strip()

    if cleaned_response.startswith('```json') and cleaned_response.endswith('```'):
        try:
            content = cleaned_response[7:-3].strip()
            return json.loads(content)
        except:
            pass

    xml_match = re.search(r'<json>(.*?)</json>', cleaned_response, re.DOTALL)
    if xml_match:
        try:
            return json.loads(xml_match.group(1).strip())
        except:
            pass

    json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass

    numbers = re.findall(r'\b\d+\b', cleaned_response)
    if len(numbers) >= 4:
        return {
            "pred_repost_count": int(numbers[0]),
            "pred_new_follower_count": int(numbers[1]),
            "pred_comment_count": int(numbers[2]),
            "pred_like_count": int(numbers[3])
        }

    return {
        "pred_repost_count": 0,
        "pred_new_follower_count": 0,
        "pred_comment_count": 0,
        "pred_like_count": 0
    }

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
    new_commenter_distribution = {}
    return new_commenter_distribution


if __name__ == '__main__':
    from backend.data.test_data import GAMER
    post_content = "煞笔游戏，再也不玩了"
    print(predict_post_stats(
        persona=GAMER.get("persona"),
        follower_count=GAMER.get("follower_count"),
        post_content=post_content,
    ))

    post_content = "明天我要开播！都来看"
    print(predict_post_stats(
        persona=GAMER.get("persona"),
        follower_count=GAMER.get("follower_count"),
        post_content=post_content,
    ))
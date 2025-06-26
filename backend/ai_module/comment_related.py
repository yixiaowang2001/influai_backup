from prompts import (
    get_generate_lv1_comments_prompt,
    get_expand_lv1_comments_prompt,
    get_generate_lvn_comments_prompt,
)
from llm import chat
from llm_utils import parse_json_response
from backend.models import Attitude
from backend.utils import get_logger

logger = get_logger("backend.ai_module.comment_related")


def generate_lv1_comments(
        persona: str,
        post_content: str,
        commenter_distribution: dict,
        each_type_n: int,
        history_posts: list = None,
        retry: int = 5
):
    system_prompt, user_prompt = get_generate_lv1_comments_prompt(
        persona=persona,
        post_content=post_content,
        commenter_distribution=commenter_distribution,
        each_type_n=each_type_n,
        history_posts=history_posts,
    )

    json_response = {"comments": []}
    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name="qwen-plus",
            temperature=1.99,
            max_tokens=4096
        )
        json_response = parse_json_response(response, {})
        if json_response and "comments" in json_response.keys():
            break

    comments_by_attitude = Attitude.create_dict()
    comments = json_response["comments"]
    for comment in comments:
        try:
            attitude = Attitude.parse(comment["attitude"])
            content = str(comment["content"])
            if not attitude or not content:
                continue
            comments_by_attitude[attitude].append(content)
        except Exception as e:
            continue
    return comments_by_attitude


def expand_lv1_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: list,
        expand_count: int
):
    system_prompt, user_prompt = get_expand_lv1_comments_prompt(
        persona=persona,
        post_content=post_content,
        attitude_type=attitude_type,
        seed_comments=seed_comments,
        expand_count=expand_count
    )

    response = chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name="qwen-plus",
        temperature=1.99,
        max_tokens=8192
    )

    print(response)


def generate_lvn_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        pre_lv_comment: str,
        expand_count: int,
        is_human_user: bool
):
    system_prompt, user_prompt = get_generate_lvn_comments_prompt(
        persona=persona,
        post_content=post_content,
        attitude_type=attitude_type,
        pre_lv_comment=pre_lv_comment,
        expand_count=expand_count,
        is_human_user=is_human_user
    )

    response = chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_name="qwen-plus",
        temperature=1.99,
        max_tokens=8192
    )

    print(response)

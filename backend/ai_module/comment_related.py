from prompts import (
    get_generate_lv1_seeds_prompt,
    get_expand_lv1_comments_prompt,
    get_generate_lvn_comments_prompt,
)
from llm import chat
from llm_utils import parse_json_response
from backend.models import Attitude
from backend.utils import get_logger

logger = get_logger("backend.ai_module.comment_related")


def generate_lv1_seeds(
        persona: str,
        post_content: str,
        history_posts: list = None,
        retry: int = 5
) -> dict:
    system_prompt, user_prompt = get_generate_lv1_seeds_prompt(
        persona=persona,
        post_content=post_content,
        history_posts=history_posts,
    )
    logger.info("Generating lv1 comments")
    json_response = {"comments": []}
    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name="qwen-plus-latest",
            temperature=1.99,
            max_tokens=8192
        )
        json_response = parse_json_response(response, {})
        if json_response and "comments" in json_response.keys():
            break
        logger.warning(f"Failed to generate lv1 comments, retrying for {i+1} time")

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
    if all(not v for v in comments_by_attitude.values()):
        logger.warning(f"Failed to generate lv1 comments, no comments found")
    else:
        logger.info("Generated lv1 comments")

    return comments_by_attitude


def expand_lv1_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: list,
        expand_count: int,
        retry: int = 5
) -> list[str]:
    logger.info(f"Expanding lv1 comments: {attitude_type}")
    system_prompt, user_prompt = get_expand_lv1_comments_prompt(
        persona=persona,
        post_content=post_content,
        attitude_type=attitude_type,
        seed_comments=seed_comments,
        expand_count=expand_count
    )

    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name="qwen-plus-latest",
            temperature=1.99,
            max_tokens=16384
        )
        json_response = parse_json_response(response, {})
        if json_response and "expansions" in json_response.keys():
            logger.info(f"lv1 comments expanded: {attitude_type}")
            return json_response["expansions"]
        logger.warning(f"Failed to expand lv1 comments for {attitude_type}, retrying for {i+1} time")
    logger.warning(f"Failed to expand lv1 comments for {attitude_type}, no comments found")

    return []


def generate_lvn_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        pre_lv_comment: str,
        expand_count: int,
        is_human_user: bool,
        retry: int = 5
) -> list[str]:
    logger.info(f"Generating lvn comments: attitude_type - {attitude_type}, pre_lv_comment - {pre_lv_comment[:20]}")
    system_prompt, user_prompt = get_generate_lvn_comments_prompt(
        persona=persona,
        post_content=post_content,
        attitude_type=attitude_type,
        pre_lv_comment=pre_lv_comment,
        expand_count=expand_count,
        is_human_user=is_human_user
    )

    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name="qwen-plus-latest",
            temperature=1.99,
            max_tokens=16384
        )
        json_response = parse_json_response(response, {})
        if json_response and "nested" in json_response.keys():
            logger.info(f"lvn comments expanded: attitude_type - {attitude_type}, pre_lv_comment - {pre_lv_comment[:20]}")
            return json_response["nested"]
        logger.warning(f"Failed to generate lvn comments for - {attitude_type}, pre_lv_comment - {pre_lv_comment[:20]}, "
                       f"retrying for {i+1} time")
    logger.warning(f"Failed to generate lvn comments for - {attitude_type}, pre_lv_comment - {pre_lv_comment}, "
                   f"no comments found")

    return []


def predict_comment_likes(
        zero_prob: float = 0.85,
        zoom_index: float = 0.1
) -> int:
    pass


def should_generate_lv2(

) -> bool:
    pass


def predict_lv2_count(

) -> int:
    pass

from backend.ai_module.llm import chat
from backend.ai_module.llm_utils import parse_json_response
from backend.ai_module.prompts import (
    get_generate_lv1_seeds_prompt,
    get_expand_lv1_comments_prompt,
    get_generate_lvn_comments_prompt,
)
from backend.models import Attitude
from backend.utils import get_logger, rand_int

logger = get_logger(__name__)


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
    logger.info("Generating level 1 seed comments")
    json_response = {"comments": []}
    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name="qwen-plus-latest",
            temperature=1.99,
            max_tokens=8192
        )
        
        if not response:
            logger.warning(f"Received empty response for level 1 seed comments, attempt {i + 1}")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "comments" in json_response.keys():
            if len(json_response["comments"]) == 18:
                break
        logger.warning(f"Failed to generate level 1 seed comments, retrying attempt {i + 1}")

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
        logger.warning(f"Failed to generate level 1 seed comments, no valid comments found")
    else:
        logger.info("Successfully generated level 1 seed comments")

    return comments_by_attitude


def expand_lv1_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: list,
        expand_count: int,
        retry: int = 5
) -> list[str]:
    logger.info(f"Expanding level 1 comments for attitude: {attitude_type}")
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
        
        if not response:
            logger.warning(f"Received empty response for level 1 comment expansion, attitude: {attitude_type}, attempt {i + 1}")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "expansions" in json_response.keys():
            logger.info(f"Successfully expanded level 1 comments for attitude: {attitude_type}")
            return json_response["expansions"]
        logger.warning(f"Failed to expand level 1 comments for attitude: {attitude_type}, retrying attempt {i + 1}")
    logger.warning(f"Failed to expand level 1 comments for attitude: {attitude_type}, no valid expansions found")

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
    logger.info(f"Generating level N comments - attitude: {attitude_type}, parent comment: {pre_lv_comment[:20]}...")
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
        
        if not response:
            logger.warning(f"Received empty response for level N comments generation, attitude: {attitude_type}, attempt {i + 1}")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "nested" in json_response.keys():
            logger.info(f"Successfully generated level N comments - attitude: {attitude_type}, parent comment: {pre_lv_comment[:20]}...")
            return json_response["nested"]
        logger.warning(f"Failed to generate level N comments - attitude: {attitude_type}, parent comment: {pre_lv_comment[:20]}..., retrying attempt {i + 1}")
    logger.warning(f"Failed to generate level N comments - attitude: {attitude_type}, parent comment: {pre_lv_comment[:20]}..., no valid nested comments found")

    return []


def predict_comment_likes(
        follower_count: int,
        float_range: float,
        zoom_index: float
) -> int:
    return rand_int(
        number=follower_count * zoom_index,
        float_range=float_range,
    )


def should_generate_lv2(

) -> bool:
    pass


def predict_lv2_count(

) -> int:
    pass


if __name__ == '__main__':
    print(predict_comment_likes(10000, 0.5, 0.001))

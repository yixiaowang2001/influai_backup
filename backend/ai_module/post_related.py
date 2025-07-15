from backend.utils import get_logger
from .llm import chat
from .llm_utils import parse_json_response
from .prompts import get_predict_post_stats_prompt

logger = get_logger(__name__)


def predict_post_stats(
        persona: str,
        follower_count: int,
        post_content: str,
        history_posts: list = None,
        retry: int = 5
) -> dict:
    logger.info("Starting post stats prediction")
    system_prompt, user_prompt = get_predict_post_stats_prompt(
        persona=persona,
        follower_count=follower_count,
        post_content=post_content,
        history_posts=history_posts,
    )
    logger.debug(f"User prompt length: {len(user_prompt)}; system prompt length: {len(system_prompt)}")

    parsed = {
        "pred_new_follower_count": 0,
        "pred_comment_count": 0,
        "pred_like_count": 0
    }

    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name="qwen-turbo",
            temperature=0.1,
            max_tokens=256
        )
        
        if not response:
            logger.warning(f"Received empty response for post stats prediction, attempt {i + 1}")
            continue
            
        parsed = parse_json_response(response, parsed)
        if parsed["pred_comment_count"] != 0:
            break
        logger.warning(f"Failed to predict post stats, retrying attempt {i + 1}")
    if parsed["pred_comment_count"] == 0:
        logger.warning(f"Failed to predict post stats, comment count is 0")
    else:
        logger.info(f"Successfully completed post stats prediction")

    return parsed


if __name__ == '__main__':
    post_content = ""

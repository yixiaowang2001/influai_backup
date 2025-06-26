from backend.utils.logger import get_logger
from llm import chat
from llm_utils import parse_json_response
from prompts import get_predict_post_stats_prompt

logger = get_logger("backend.ai_module.post_related")


def predict_post_stats(
        persona: str,
        follower_count: int,
        post_content: str,
        history_posts: list = None,
):
    logger.info("Starting post stats prediction")
    system_prompt, user_prompt = get_predict_post_stats_prompt(
        persona=persona,
        follower_count=follower_count,
        post_content=post_content,
        history_posts=history_posts,
    )
    logger.debug(f"User prompt length: {len(user_prompt)}; system prompt length: {len(system_prompt)}")
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

    if not response:
        logger.warning("Using default response due to empty LLM output (predict_post_stats)")
        return default_response
    parsed = parse_json_response(response, default_response)
    logger.info(f"Successfully get response (predict_post_stats)")
    return parsed


if __name__ == '__main__':
    post_content = ""

    # print(predict_post_stats(
    #     persona=GAMER["persona"],
    #     follower_count=GAMER["follower_count"],
    #     post_content=post_content,
    # ))
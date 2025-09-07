from typing import Dict, List, Optional

from backend.utils import get_logger
from .llm import chat
from .llm_utils import parse_json_response
from .prompts import get_predict_post_stats_prompt

logger = get_logger(__name__)


def predict_post_stats(
        persona: str,
        follower_count: int,
        post_content: str,
        history_posts: Optional[List[str]] = None,
        retry: int = 5
) -> Dict[str, int]:
    """
    预测帖子统计数据
    
    Args:
        persona: 用户人设
        follower_count: 粉丝数量
        post_content: 帖子内容
        history_posts: 历史帖子列表
        retry: 重试次数
        
    Returns:
        Dict[str, int]: 预测的统计数据
    """
    logger.info("开始预测帖子统计数据")
    system_prompt, user_prompt = get_predict_post_stats_prompt(
        persona=persona,
        follower_count=follower_count,
        post_content=post_content,
        history_posts=history_posts,
    )
    logger.debug(f"用户提示词长度: {len(user_prompt)}; 系统提示词长度: {len(system_prompt)}")

    parsed = {
        "pred_new_follower_count": 0,
        "pred_comment_count": 0,
        "pred_like_count": 0
    }

    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config_type="post_stats"
        )
        
        if not response:
            logger.warning(f"收到空的帖子统计预测响应，第{i + 1}次尝试")
            continue
            
        parsed = parse_json_response(response, parsed)
        if parsed["pred_comment_count"] != 0:
            break
        logger.warning(f"预测帖子统计失败，第{i + 1}次重试")
    if parsed["pred_comment_count"] == 0:
        logger.warning(f"预测帖子统计失败，评论数为0")
    else:
        logger.info(f"成功完成帖子统计预测")

    return parsed


if __name__ == '__main__':
    post_content = ""

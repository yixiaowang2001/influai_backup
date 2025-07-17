from typing import Dict, List, Optional

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
COMMENT_RELATED_MODEL = "qwen-plus-2025-01-25"
MAX_TOKEN = 8192


def generate_lv1_seeds(
        persona: str,
        post_content: str,
        history_posts: Optional[List[str]] = None,
        retry: int = 5
) -> Dict[Attitude, List[str]]:
    """
    生成一级种子评论
    
    Args:
        persona: 用户人设
        post_content: 帖子内容
        history_posts: 历史帖子列表
        retry: 重试次数
        
    Returns:
        Dict[Attitude, List[str]]: 按态度分类的种子评论
    """
    system_prompt, user_prompt = get_generate_lv1_seeds_prompt(
        persona=persona,
        post_content=post_content,
        history_posts=history_posts,
    )
    logger.info("生成一级种子评论")
    json_response = {"comments": []}
    for i in range(retry):
        response = chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=COMMENT_RELATED_MODEL,
            temperature=1.99,
            max_tokens=MAX_TOKEN
        )
        
        if not response:
            logger.warning(f"收到空的一级种子评论响应，第{i + 1}次尝试")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "comments" in json_response.keys():
            if len(json_response["comments"]) == 18:
                break
        logger.warning(f"生成一级种子评论失败，第{i + 1}次重试")

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
        logger.warning(f"生成一级种子评论失败，未找到有效评论")
    else:
        logger.info("成功生成一级种子评论")

    return comments_by_attitude


def expand_lv1_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        seed_comments: List[str],
        expand_count: int,
        retry: int = 5
) -> List[str]:
    """
    扩展一级评论
    
    Args:
        persona: 用户人设
        post_content: 帖子内容
        attitude_type: 态度类型
        seed_comments: 种子评论列表
        expand_count: 扩展数量
        retry: 重试次数
        
    Returns:
        List[str]: 扩展后的评论列表
    """
    logger.info(f"扩展一级评论，态度: {attitude_type}")
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
            model_name=COMMENT_RELATED_MODEL,
            temperature=1.99,
            max_tokens=MAX_TOKEN
        )
        
        if not response:
            logger.warning(f"收到空的一级评论扩展响应，态度: {attitude_type}，第{i + 1}次尝试")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "expansions" in json_response.keys():
            logger.info(f"成功扩展一级评论，态度: {attitude_type}")
            return json_response["expansions"]
        logger.warning(f"扩展一级评论失败，态度: {attitude_type}，第{i + 1}次重试")
    logger.warning(f"扩展一级评论失败，态度: {attitude_type}，未找到有效扩展")

    return []


def generate_lvn_comments(
        persona: str,
        post_content: str,
        attitude_type: Attitude,
        pre_lv_comment: str,
        expand_count: int,
        is_human_user: bool,
        retry: int = 5
) -> List[str]:
    """
    生成N级评论
    
    Args:
        persona: 用户人设
        post_content: 帖子内容
        attitude_type: 态度类型
        pre_lv_comment: 上级评论
        expand_count: 扩展数量
        is_human_user: 是否为人类用户
        retry: 重试次数
        
    Returns:
        List[str]: 生成的N级评论列表
    """
    logger.info(f"生成N级评论 - 态度: {attitude_type}，父评论: {pre_lv_comment[:20]}...")
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
            model_name=COMMENT_RELATED_MODEL,
            temperature=1.99,
            max_tokens=MAX_TOKEN
        )
        
        if not response:
            logger.warning(f"收到空的N级评论生成响应，态度: {attitude_type}，第{i + 1}次尝试")
            continue
            
        json_response = parse_json_response(response, {})
        if json_response and "nested" in json_response.keys():
            logger.info(f"成功生成N级评论 - 态度: {attitude_type}，父评论: {pre_lv_comment[:20]}...")
            return json_response["nested"]
        logger.warning(f"生成N级评论失败 - 态度: {attitude_type}，父评论: {pre_lv_comment[:20]}...，第{i + 1}次重试")
    logger.warning(f"生成N级评论失败 - 态度: {attitude_type}，父评论: {pre_lv_comment[:20]}...，未找到有效嵌套评论")

    return []


def predict_comment_likes(
        follower_count: int,
        float_range: float,
        zoom_index: float
) -> int:
    """
    预测评论点赞数
    
    Args:
        follower_count: 粉丝数量
        float_range: 浮动范围
        zoom_index: 缩放指数
        
    Returns:
        int: 预测的点赞数
    """
    return rand_int(
        number=follower_count * zoom_index,
        float_range=float_range,
    )


def should_generate_lv2() -> bool:
    """判断是否应该生成二级评论"""
    pass


def predict_lv2_count() -> int:
    """预测二级评论数量"""
    pass


if __name__ == '__main__':
    print(predict_comment_likes(10000, 0.5, 0.001))

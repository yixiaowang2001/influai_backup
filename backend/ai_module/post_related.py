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
    pred_repost_count = 0
    pred_new_follower_count = 0
    pred_comment_count = 0
    pred_like_count = 0
    return pred_repost_count, pred_new_follower_count, pred_comment_count, pred_like_count


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
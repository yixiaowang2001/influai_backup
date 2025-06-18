def predict_human_user_current_post_stats(
        human_user_persona: str,
        human_user_follower_count: int,
        post_content: str,
        history_posts: list = None,
):
    """
    基于以下信息，预测人类用户当前的帖子会有多少转发、新增关注、评论、点赞数量。
    :param human_user_persona: 人类用户人设
    :param human_user_follower_count: 新增关注数量
    :param post_content: 帖子内容
    :param history_posts: 历史帖子内容
    :return: 预测转发量，预测新增关注量，预测评论量，预测点赞量
    """
    pred_repost_count = 0
    pred_new_follower_count = 0
    pred_comment_count = 0
    pred_like_count = 0
    return pred_repost_count, pred_new_follower_count, pred_comment_count, pred_like_count


def update_human_user_commenter_distribution(
        prev_commenter_distribution: dict,
        human_user_persona: str,
        post_content: str,
        history_posts: list = None,
):
    """
    基于以下信息，更新人类用户评论者分布。
    :param prev_commenter_distribution: 旧评论者分布
    :param human_user_persona: 人类用户人设
    :param post_content: 帖子内容
    :param history_posts: 历史帖子内容
    :return: 新评论者分布
    """
    new_commenter_distribution = {}
    return new_commenter_distribution


def generate_level1_comments(
        human_user_persona: str,
        commenter_type: list,
        post_content: str,
        each_type_n: int,
        history_posts: list = None,
):
    """
    基于以下信息，生成level1评论
    :param human_user_persona: 人类用户人设
    :param commenter_type: 评论者类别（来源于分布的key）
    :param post_content: 帖子内容
    :param history_posts: 历史帖子
    :param each_type_n: 每个评论者类别生成的评论数量
    :return: 生成的所有评论
    """
    gen_l1_comments = []
    return gen_l1_comments


def generate_similar_level1_comments(
        post_content: str,
        ref_comment_content: str,
        n: int,
):
    """
    基于以下信息，生成情感相似level1评论
    :param post_content: 帖子内容
    :param ref_comment_content: 参考评论
    :param n: 生成评论数量
    :return: 生成的相似评论
    """
    similar_comments = []
    return similar_comments


def generate_level2_comments(
        post_content: str,
        level1_comment: str,
        n: int,
):
    """
    基于以下信息，生成level2评论
    :param post_content: 帖子信息
    :param level1_comment: level1评论（单条）
    :param commenter_type: 评论者类别（来源于分布的key）
    :param n: 生成评论数量
    :return: 生成的level2评论
    """
    gen_l2_comments = []
    return gen_l2_comments


def generate_similar_level2_comments(
        post_conetent
):
    pass
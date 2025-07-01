from post_related import predict_post_stats
from comment_related import (
    generate_lv1_seeds,
    expand_lv1_comments,
    generate_lvn_comments,
    predict_comment_likes,
    should_generate_lv2,
    predict_lv2_count
)
from backend.data.test_data import INFLUENCER as USER


def workflow(
        post_content
):
    persona = USER["persona"]
    follower_count = USER["follower_count"]
    commenter_distribution = USER["commenter_distribution"]
    history_posts = None

    post_stats = predict_post_stats(
        persona=persona,
        follower_count=follower_count,
        post_content=post_content,
        history_posts=history_posts,
    )

    print(post_stats)

    if post_stats["pred_comment_count"] == 0:
        print("Pre comment count = 0")
        return

    lv1_comments = generate_lv1_seeds(
        persona=persona,
        post_content=post_content,
        commenter_distribution=commenter_distribution,
        each_type_n=5,
        retry=5
    )


if __name__ == "__main__":
    post_content = """你好
"""
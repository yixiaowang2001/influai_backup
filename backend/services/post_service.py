from backend.models import Post
from backend.utils import get_logger
from backend.ai_module import (
    predict_post_stats,
    generate_lv1_seeds,
    expand_lv1_comments
)
from backend.configs import RETRY_COUNT
from backend.models import Attitude
from .service_utils import rand_int
from tqdm import tqdm

logger = get_logger("backend.services.post_service")


class PostService:
    def __init__(
            self,
            content: str,
            user_template: dict,
            history_posts: list
    ):
        self.post = Post(
            post_content=content
        )
        self.user_template = user_template
        self.history_posts = history_posts
        self.lv1_seeds = None
        self.new_follower_count = None
        self.pred_comment_count = None
        self.comments = []

    def basic_update(self):
        stats = predict_post_stats(
            persona=self.user_template["persona"],
            follower_count=self.user_template["follower_count"],
            post_content=self.post.post_content,
            history_posts=self.history_posts,
            retry=RETRY_COUNT
        )
        self.post.like_count = stats["pred_like_count"]
        self.new_follower_count = stats["pred_new_follower_count"]
        self.pred_comment_count = stats["pred_comment_count"]
        self.lv1_seeds = generate_lv1_seeds(
            persona=self.user_template["persona"],
            post_content=self.post.post_content,
            history_posts=self.history_posts,
            retry=RETRY_COUNT
        )

    def expand_lv1_comments_by_attitude(
            self,
            attitude: Attitude,
            num: int
    ):
        short_num = rand_int(num / 3)
        medium_num = rand_int(num / 3)
        long_num = num - short_num - medium_num
        num_list = [short_num, medium_num, long_num]

        comments = []

        for i in range(3):
            generate_comments = expand_lv1_comments(
                persona=self.user_template["persona"],
                post_content=self.post.post_content,
                attitude_type=attitude,
                seed_comments=self.lv1_seeds[attitude][i],
                expand_count=num_list[i],
                retry=RETRY_COUNT
            )
            comments.extend(generate_comments)

        return comments

    def run(self):
        self.basic_update()

        for att in tqdm(Attitude.create_dict().keys()):
            comment_count = round(self.pred_comment_count * self.user_template["commenter_distribution"][att])
            self.comments.extend(self.expand_lv1_comments_by_attitude(att, comment_count))

        print(self.comments)

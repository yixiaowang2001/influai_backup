from tqdm import tqdm

from backend.ai_module import (
    predict_post_stats,
    generate_lv1_seeds,
    expand_lv1_comments,
    predict_comment_likes
)
from backend.configs import RETRY_COUNT, MAX_COMMENTS_PER_REQUEST
from backend.database import database
from backend.models import Attitude, Comment
from backend.models import Post
from backend.utils import get_logger, rand_int, format_history_posts
from backend.database.crud import (
    create_post,
    create_comment,
    create_ai_user,
    get_latest_n_posts
)
from backend.database.database import get_db_session
from backend.database.init_db import init_database
from backend.models import (
    Post,
    Comment,
    AIUser,
    Attitude
)

logger = get_logger(__name__)


class PostService:
    def __init__(
            self,
            content: str,
            user_template: dict,
            db,
    ):
        self.post = Post(
            post_content=content,
        )
        self.user_template = user_template
        self.db = db
        self.lv1_seeds = None
        self.new_follower_count = None
        self.pred_comment_count = None
        self.comments = []
        self.history_posts = []

    def distribute_comment_nums(
            self,
            total: int,
    ) -> dict:
        ratios = self.user_template["commenter_distribution"]
        total_ratio = sum(ratios.values())
        result = {}
        fractional_parts = []
        allocated = 0

        for key, ratio in ratios.items():
            exact_value = total * ratio / total_ratio
            integer_part = int(exact_value)
            result[key] = integer_part
            allocated += integer_part
            fractional_parts.append((exact_value - integer_part, key))

        remaining = total - allocated
        if remaining > 0:
            fractional_parts.sort(key=lambda x: x[0], reverse=True)
            for i in range(remaining):
                _, key = fractional_parts[i]
                result[key] += 1

        return result

    def basic_update(self):
        self.history_posts = format_history_posts(get_latest_n_posts(
            db=self.db,
            n=3
        ))
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
    ) -> list:
        if num == 0:
            logger.warning("No comments need to be expanded")
            return []
        short_num = rand_int(num / 3)
        medium_num = rand_int(num / 3)
        long_num = num - short_num - medium_num
        num_list = [short_num, medium_num, long_num]
        comments = []
        logger.debug(f"For {attitude}, num_list is {num_list}")

        for i in range(3):
            target_count = num_list[i]
            generated_count = 0
            attitude_comments = []

            while generated_count < target_count:
                current_batch = min(MAX_COMMENTS_PER_REQUEST, target_count - generated_count)
                batch_comments = expand_lv1_comments(
                    persona=self.user_template["persona"],
                    post_content=self.post.post_content,
                    attitude_type=attitude,
                    seed_comments=self.lv1_seeds[attitude][i],
                    expand_count=current_batch,
                    retry=RETRY_COUNT
                )
                if not batch_comments:
                    logger.warning("No batch_comments generated")
                    break
                generated_count += len(batch_comments)
                attitude_comments.extend(batch_comments)
                if generated_count >= target_count * 2:
                    break
            if generated_count > target_count:
                attitude_comments = attitude_comments[:target_count]

            logger.debug(f"For {attitude}, {len(attitude_comments)} comments generated")
            for ac in attitude_comments:
                comment = Comment(
                    comment_content=ac,
                    comment_user_type=0,
                    comment_attitude=attitude,
                    comment_level=1,
                    comment_likes=predict_comment_likes(
                        follower_count=self.user_template["follower_count"],
                        float_range=0.9,
                        zoom_index=0.01
                    )
                )
                comments.append(comment)
        return comments

    def run(self):
        self.basic_update()
        post = create_post(self.db, self.post)

        logger.info("PostService initialized")
        logger.info(f"Start to generate {self.pred_comment_count} comments...")
        comment_nums_by_attitude = self.distribute_comment_nums(total=self.pred_comment_count)
        for att in tqdm(Attitude.create_dict().keys()):
            comment_count = comment_nums_by_attitude[str(att)]
            expanded_comments = self.expand_lv1_comments_by_attitude(att, comment_count)
            for comment in expanded_comments:
                comment.post_id = post.post_id
                self.comments.append(comment)
                create_comment(self.db, comment)

        logger.info(f"{len(self.comments)} comments generated.")

        print(self.comments)

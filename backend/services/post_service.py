from typing import List, Dict, Any
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
from backend.utils import get_logger, rand_int, format_history_posts, distribute_by_ratio
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
    """帖子服务类，负责处理帖子的创建和评论生成"""
    
    def __init__(
            self,
            content: str,
            user_template: Dict[str, Any],
            db,
    ):
        """
        初始化帖子服务
        
        Args:
            content: 帖子内容
            user_template: 用户模板配置
            db: 数据库会话
        """
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
    ) -> Dict[str, int]:
        """
        根据用户模板分配评论数量
        
        Args:
            total: 总评论数
            
        Returns:
            Dict[str, int]: 各态度类型的评论数量分布
        """
        return distribute_by_ratio(total, self.user_template["commenter_distribution"])

    def basic_update(self) -> None:
        """执行基础更新操作，包括预测统计数据和生成种子评论"""
        self.history_posts = format_history_posts(get_latest_n_posts(
            db=self.db,
            n=3
        ), 3)
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
    ) -> List[Comment]:
        """
        根据态度类型扩展一级评论
        
        Args:
            attitude: 态度类型
            num: 评论数量
            
        Returns:
            List[Comment]: 扩展后的评论列表
        """
        if num == 0:
            logger.warning("无需扩展评论")
            return []
        short_num = rand_int(num / 3)
        medium_num = rand_int(num / 3)
        long_num = num - short_num - medium_num
        num_list = [short_num, medium_num, long_num]
        comments = []
        logger.debug(f"对于{attitude}，数量列表为{num_list}")

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
                    logger.warning("未生成批量评论")
                    break
                generated_count += len(batch_comments)
                attitude_comments.extend(batch_comments)
                if generated_count >= target_count * 2:
                    break
            if generated_count > target_count:
                attitude_comments = attitude_comments[:target_count]

            logger.debug(f"对于{attitude}，生成了{len(attitude_comments)}条评论")
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

    def run(self) -> None:
        """运行帖子服务，创建帖子并生成评论"""
        self.basic_update()
        post = create_post(self.db, self.post)

        logger.info("帖子服务已初始化")
        logger.info(f"开始生成{self.pred_comment_count}条评论...")
        comment_nums_by_attitude = self.distribute_comment_nums(total=self.pred_comment_count)
        for att in tqdm(Attitude.create_dict().keys()):
            comment_count = comment_nums_by_attitude[str(att)]
            expanded_comments = self.expand_lv1_comments_by_attitude(att, comment_count)
            for comment in expanded_comments:
                comment.post_id = post.post_id
                self.comments.append(comment)
                create_comment(self.db, comment)

        logger.info(f"生成了{len(self.comments)}条评论。")

        logger.info(f"生成的评论详情: {self.comments}")

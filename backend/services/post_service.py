from typing import List, Dict, Any, Union

from tqdm import tqdm

from backend.ai_module import (
    predict_post_stats,
    generate_lv1_seeds,
    expand_lv1_comments,
    predict_comment_likes
)
from backend.configs import RETRY_COUNT, MAX_COMMENTS_PER_REQUEST
from backend.database import models as db_models
from backend.database.crud import (
    create_post,
    create_comment,
    get_latest_n_posts,
    get_available_ai_users_by_attitude,
    get_user_template_by_name,
    get_user_template_by_id
)
from backend.models import (
    Post,
    Attitude
)
from backend.utils import get_logger, rand_int, format_history_posts, distribute_by_ratio

logger = get_logger(__name__)


class PostService:
    """帖子服务类，负责处理帖子的创建和评论生成"""

    def __init__(
            self,
            content: str,
            template_name: str = None,
            template_id: int = None,
            human_user_id: int = None,
            db = None,
    ):
        """
        初始化帖子服务
        
        Args:
            content: 帖子内容
            template_name: 用户模板名称（与template_id二选一）
            template_id: 用户模板ID（与template_name二选一）
            human_user_id: 人类用户ID，用于限制AI用户选择范围
            db: 数据库会话
        """
        self.post = Post(
            post_content=content,
            is_human_user_liked=0  # 新帖子默认未点赞
        )
        self.template_name = template_name
        self.template_id = template_id
        self.human_user_id = human_user_id
        self.db = db
        self.user_template = None
        self.lv1_seeds = None
        self.new_follower_count = None
        self.pred_comment_count = None
        self.comments = []
        self.history_posts = []
        self.assigned_ai_users = set()  # 记录已分配的AI用户ID

        # 从数据库加载用户模板
        self._load_user_template()

    def _load_user_template(self):
        """从数据库加载用户模板"""
        if self.template_id is not None:
            template = get_user_template_by_id(self.db, self.template_id)
            if not template:
                raise ValueError(f"未找到模板ID: {self.template_id}")
        elif self.template_name is not None:
            template = get_user_template_by_name(self.db, self.template_name)
            if not template:
                raise ValueError(f"未找到模板: {self.template_name}")
        else:
            raise ValueError("必须提供template_name或template_id")

        # 将数据库对象转换为字典格式，保持与原有代码的兼容性
        self.user_template = {
            "persona": template.persona,
            "follower_count": template.follower_count,
            "commenter_distribution": template.commenter_distribution,
            "default_avatar_path": template.default_avatar_path
        }

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

    def assign_ai_user_to_comment(self, comment: db_models.Comment, attitude: Attitude) -> Union[Any, None]:
        """
        为评论分配AI用户（按态度匹配）
        
        Args:
            comment: 评论对象
            attitude: 评论的态度类型
            
        Returns:
            str: 分配的AI用户ID
        """
        import random
        import math

        # 获取对应态度的AI用户
        available_users = get_available_ai_users_by_attitude(
            db=self.db,
            attitude_type=attitude,  # 按态度过滤
            exclude_user_ids=list(self.assigned_ai_users)
        )

        # 如果指定了human_user_id，只选择该人类用户的AI用户
        if self.human_user_id is not None:
            available_users = [user for user in available_users if user.human_user_id == self.human_user_id]

        if not available_users:
            logger.warning(f"没有可用的{attitude}态度AI用户" + (f"，人类用户ID: {self.human_user_id}" if self.human_user_id else ""))
            # 如果没有可用用户，重置已分配用户列表（允许重复分配）
            self.assigned_ai_users.clear()
            available_users = get_available_ai_users_by_attitude(
                db=self.db,
                attitude_type=attitude  # 按态度过滤
            )
            
            # 再次过滤human_user_id
            if self.human_user_id is not None:
                available_users = [user for user in available_users if user.human_user_id == self.human_user_id]
            
            if not available_users:
                logger.error(f"数据库中没有任何{attitude}态度的AI用户" + (f"，人类用户ID: {self.human_user_id}" if self.human_user_id else ""))
                return None

        # 计算每个用户的权重（基于态度值的绝对值）
        weights = []
        for user in available_users:
            # 态度值绝对值越大，权重越高
            weight = abs(user.attitude_value)
            # 使用指数函数增加权重差异，但不至于过于极端
            weight = math.exp(weight * 2)  # 乘以2是为了增加差异，可以根据需要调整
            weights.append(weight)

        # 使用加权随机选择
        selected_user = random.choices(available_users, weights=weights, k=1)[0]

        # 记录已分配的用户
        self.assigned_ai_users.add(selected_user.user_id)

        logger.debug(f"为评论分配AI用户: {selected_user.username} (态度值: {selected_user.attitude_value}, 人类用户ID: {selected_user.human_user_id})")

        return selected_user.user_id

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
        
        # 生成种子评论
        raw_lv1_seeds = generate_lv1_seeds(
            persona=self.user_template["persona"],
            post_content=self.post.post_content,
            history_posts=self.history_posts,
            retry=RETRY_COUNT
        )
        
        # 将种子评论转换为嵌套格式（每个态度对应3个列表：短、中、长）
        self.lv1_seeds = {}
        for attitude, comments in raw_lv1_seeds.items():
            if comments:
                # 将评论分成3组
                total_comments = len(comments)
                short_count = max(1, total_comments // 3)
                medium_count = max(1, total_comments // 3)
                long_count = total_comments - short_count - medium_count
                
                self.lv1_seeds[attitude] = [
                    comments[:short_count],  # 短评论
                    comments[short_count:short_count + medium_count],  # 中评论
                    comments[short_count + medium_count:]  # 长评论
                ]
            else:
                # 如果没有评论，创建空的占位符
                self.lv1_seeds[attitude] = [["默认评论"], ["默认评论"], ["默认评论"]]

    def expand_lv1_comments_by_attitude(
            self,
            attitude: Attitude,
            num: int
    ) -> List[db_models.Comment]:
        """
        根据态度类型扩展一级评论
        
        Args:
            attitude: 态度类型
            num: 评论数量
            
        Returns:
            List[db_models.Comment]: 扩展后的评论列表
        """
        if num == 0:
            logger.warning(f"态度 {attitude} 无需扩展评论")
            return []
        
        # 确保num至少为1，避免除以3后过小
        if num < 3:
            # 如果数量太少，直接分配
            if num == 1:
                short_num = 1
                medium_num = 0
                long_num = 0
            elif num == 2:
                short_num = 1
                medium_num = 1
                long_num = 0
        else:
            # 正常分配逻辑
            short_num = max(1, rand_int(num / 3))
            medium_num = max(1, rand_int(num / 3))
            long_num = max(0, num - short_num - medium_num)
            
            # 确保总数不超过num
            total = short_num + medium_num + long_num
            if total > num:
                # 按比例调整
                if total > 0:
                    short_num = max(1, int(short_num * num / total))
                    medium_num = max(1, int(medium_num * num / total))
                    long_num = num - short_num - medium_num
        
        num_list = [short_num, medium_num, long_num]
        comments = []
        logger.debug(f"对于{attitude}，数量列表为{num_list}")

        for i in range(3):
            target_count = num_list[i]
            if target_count == 0:
                logger.debug(f"态度 {attitude} 的第 {i} 组目标数量为0，跳过")
                continue
            generated_count = 0
            attitude_comments = []

            while generated_count < target_count:
                current_batch = min(MAX_COMMENTS_PER_REQUEST, target_count - generated_count)
                
                # 检查种子评论是否可用
                seed_comments = self.lv1_seeds[attitude][i]
                if not seed_comments or seed_comments == ["默认评论"]:
                    logger.warning(f"态度 {attitude} 的第 {i} 组种子评论不可用，跳过")
                    break
                
                batch_comments = expand_lv1_comments(
                    persona=self.user_template["persona"],
                    post_content=self.post.post_content,
                    attitude_type=attitude,
                    seed_comments=seed_comments,
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
                comment = db_models.Comment(
                    comment_content=ac,
                    comment_user_type=0,
                    comment_level=1,
                    comment_likes=predict_comment_likes(
                        follower_count=self.user_template["follower_count"],
                        float_range=0.9,
                        zoom_index=0.01
                    ),
                    is_human_user_liked=0,  # AI生成的评论默认未点赞
                    sender_type="ai_user",  # 设置为AI用户类型
                    sender_id=""  # 稍后分配AI用户ID
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
                ai_user_id = self.assign_ai_user_to_comment(comment, att)
                if ai_user_id:
                    comment.sender_id = ai_user_id
                self.comments.append(comment)
                create_comment(self.db, comment)

        logger.info(f"生成了{len(self.comments)}条评论。")

        logger.info(f"生成的评论详情: {self.comments}")

    def generate_comments_for_existing_post(self, post_id: int) -> None:
        """为已存在的帖子生成评论"""
        self.basic_update()
        
        logger.info("帖子服务已初始化")
        logger.info(f"开始为帖子 {post_id} 生成{self.pred_comment_count}条评论...")
        comment_nums_by_attitude = self.distribute_comment_nums(total=self.pred_comment_count)
        for att in tqdm(Attitude.create_dict().keys()):
            comment_count = comment_nums_by_attitude[str(att)]
            expanded_comments = self.expand_lv1_comments_by_attitude(att, comment_count)
            for comment in expanded_comments:
                comment.post_id = post_id
                ai_user_id = self.assign_ai_user_to_comment(comment, att)
                if ai_user_id:
                    comment.sender_id = ai_user_id
                self.comments.append(comment)
                create_comment(self.db, comment)

        logger.info(f"为帖子 {post_id} 生成了{len(self.comments)}条评论。")

        logger.info(f"生成的评论详情: {self.comments}")
        
        # 返回预测的统计数据，供调用者更新帖子
        return {
            "pred_like_count": self.post.like_count,
            "pred_comment_count": self.pred_comment_count,
            "new_follower_count": self.new_follower_count
        }

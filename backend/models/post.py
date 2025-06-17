from datetime import datetime


class Post:
    def __init__(
            self,
            postid: int,
            post_content: str,
            repost_count: list,  # 后续支持详细repost，替换成reposts
            like_count: int,
            comments: list,
            upvote_count: int,
            created_at: datetime = None,
            edited_at: datetime = None,
    ):
        self.postid = postid
        self.post_content = post_content
        self.repost_count = repost_count
        self.like_count = like_count
        self.comments = comments
        self.upvote_count = upvote_count
        self.created_at = created_at
        self.edited_at = edited_at

from datetime import datetime


class HumanUser:
    def __init__(
            self,
            userid: int,
            username: str,
            avatar: str = "",
            persona: str = "",
            description: str = "",
            follower_count: int = 0,
            history_posts: list = None,
            created_at: datetime = None,
    ):
        self.userid = userid
        self.username = username
        self.avatar = avatar
        self.persona = persona
        self.description = description
        self.follower_count = follower_count  # 后续支持详细follower，替换成followers
        self.history = history_posts
        self.created_at = created_at

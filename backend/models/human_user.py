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
            commenter_distribution: dict = None,
            history_posts: list = None,
            created_at: datetime = None,
    ):
        self.userid = userid
        self.username = username
        self.avatar = avatar
        self.persona = persona
        self.description = description
        self.follower_count = follower_count
        self.commenter_distribution = commenter_distribution
        self.history = history_posts
        self.created_at = created_at

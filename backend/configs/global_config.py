# 调试模式开关
IS_DEBUG = False
# 重试次数
RETRY_COUNT = 5
# 每次请求最大评论数
MAX_COMMENTS_PER_REQUEST = 50

# 推送配置
PUSH_CONFIG = {
    "comment": {
        "total_duration": 120,  # 总推送时间（秒）
        "base_interval": 5.0,  # 基础间隔（秒）
        "random_variance": 0.3,  # 随机波动比例（30%）
        "initial_delay": 1.0  # 初始延迟（秒）
    },
    "like": {
        "total_duration": 180,  # 总推送时间（秒）
        "base_interval": 8.0,  # 基础间隔（秒）
        "random_variance": 0.3,  # 随机波动比例（30%）
        "initial_delay": 0.5  # 初始延迟（秒）
    }
}

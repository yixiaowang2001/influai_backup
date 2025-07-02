from backend.data.test_data import INFLUENCER as USER
from backend.services.post_service import PostService
from backend.utils import get_logger

logger = get_logger("backend.services.core")

template = USER

post = """最让我心被掏空的是那些质疑的目光和随时燃起的评论区战火。每一次推荐，背脊都下意识绷紧，预演着下一秒会砸过来的“又是广告吧？”或者“收了
多少钱？”每一次风波我都沉默，把解释咽下去，维持那个冰冷的“工具人”体面。连坦诚标注都成了奢侈，只因为害怕那点脆弱的信任彻底崩解。我原以为爱的是分
享好物，现在却被困在数据和信任的夹缝里动弹不得。血液里流的，好像不再是当初看见一抹好唇色时的悸动，而是累，深不见底、连眼眶都涩得掉不下泪的心累。"""

ps = PostService(
    content=post,
    user_template=template,
    history_posts=[]
)
ps.run()

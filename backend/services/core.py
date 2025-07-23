from backend.database.database import get_db_session
from backend.database.init_db import init_database
from backend.services.post_service import PostService
from backend.utils import get_logger

logger = get_logger(__name__)

# 用户模板配置
template_name = "CASTER"

# 测试帖子内容
post = """老胡像大家一样痛恨虐猫者，支持对他们做出应有的惩罚。我只是建议，在惩罚之后，舆论不要长期"追杀"他们，其实，我觉得对各种犯了错，哪怕刑满释放人员，舆论都不要"追杀"，让法律和规定，以及那些人生活的周围环境决定他们之后的命运，尤其是对于非公众人物，非官员，要给他们悔过自新的机会。

不要让我们的社会过度严厉，各种处罚应尽量依法依规，不附加，尤其是不长期附加法律法规没有要求的额外处罚，这是老胡的一贯主张。对老胡的观点可以反对，但老胡必须申明的是，我决无冒犯任何群体、包括爱猫和动保群体的意思[作揖][作揖]      #招聘单位回应考生确系虐猫当事人#    #热点解读#"""

# 初始化数据库
init_database(
    template_name=template_name,
)

# 获取数据库会话
db = get_db_session()

logger.info("数据库已初始化")

# 创建帖子服务实例并运行
ps = PostService(
    content=post,
    template_name=template_name,
    db=db
)
ps.run()

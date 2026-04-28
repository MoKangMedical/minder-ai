#!/usr/bin/env python3
"""
Minder AI红娘 - 综合演示数据生成脚本

创建完整的演示环境：
  - 30个真实用户 (15男 15女)
  - 20条匹配记录
  - 10个对话线程 (含消息)
  - 5份健康报告
  - 3条订阅记录

用法:
  cd ~/Desktop/婚恋AI && python3 -m minder.scripts.seed_data
  cd ~/Desktop/婚恋AI && python3 -m minder.scripts.seed_data --reset
"""

import asyncio
import sys
import os
import random
import hashlib
from datetime import datetime, timedelta

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from minder.db.models import (
    Base, engine, async_session,
    User, UserPhoto, Match, Message, HealthReport, Subscription, Report,
    Gender, SubscriptionTier, MatchStatus, ReportReason,
)

# ============================================================
# Demo password hash (bcrypt is slow, use a fast hash for seeding)
# In production this would be bcrypt. For demo: "Demo123456!"
# ============================================================
DEMO_PASSWORD_HASH = hashlib.sha256("Demo123456!".encode()).hexdigest()


# ============================================================
# 30 Realistic Users - 15 Male, 15 Female
# ============================================================
MALE_USERS = [
    {
        "phone": "13900001001",
        "nickname": "陈志远",
        "gender": Gender.MALE,
        "birth_date": datetime(1993, 5, 12),
        "city": "北京",
        "bio": "热爱旅行和摄影，去过20多个国家，希望找到志同道合的另一半。目前在一家互联网公司做产品总监，工作之余最大的爱好就是背着相机到处走。",
        "occupation": "产品总监",
        "education": "北京大学 硕士",
        "height_cm": 178,
        "personality_tags": ["外向", "乐观", "有责任感", "幽默"],
        "values_tags": ["事业心强", "追求品质生活", "重视家庭"],
        "lifestyle_tags": ["旅行", "摄影", "健身", "阅读"],
    },
    {
        "phone": "13900001002",
        "nickname": "王浩然",
        "gender": Gender.MALE,
        "birth_date": datetime(1995, 8, 23),
        "city": "上海",
        "bio": "复旦计算机硕士，AI创业公司CTO。工作日写代码，周末打篮球或玩摄影。不是只会写代码的宅男，也喜欢户外运动和美食探店。",
        "occupation": "CTO / 技术合伙人",
        "education": "复旦大学 硕士",
        "height_cm": 180,
        "personality_tags": ["理性", "上进", "有担当", "幽默"],
        "values_tags": ["事业心强", "追求成长", "独立自主"],
        "lifestyle_tags": ["篮球", "摄影", "编程", "健身", "美食"],
    },
    {
        "phone": "13900001003",
        "nickname": "李明轩",
        "gender": Gender.MALE,
        "birth_date": datetime(1991, 2, 14),
        "city": "深圳",
        "bio": "创业中，做跨境电商。虽然工作很忙，但相信爱情值得等待。喜欢跑步和看书，偶尔会弹吉他放松一下。周末也喜欢去大梅沙看海。",
        "occupation": "创业者",
        "education": "中山大学 本科",
        "height_cm": 175,
        "personality_tags": ["有梦想", "坚韧", "独立", "浪漫"],
        "values_tags": ["事业心强", "追求自由", "家庭优先"],
        "lifestyle_tags": ["跑步", "阅读", "吉他", "旅行", "海边"],
    },
    {
        "phone": "13900001004",
        "nickname": "张天宇",
        "gender": Gender.MALE,
        "birth_date": datetime(1994, 4, 28),
        "city": "杭州",
        "bio": "阿里高级工程师，标准程序员一枚。不过我不是那种只会写代码的宅男，周末会去骑行或者约朋友打球。偶尔也会下厨做几道菜。",
        "occupation": "高级工程师",
        "education": "浙江大学 硕士",
        "height_cm": 176,
        "personality_tags": ["踏实", "聪明", "有趣", "有上进心"],
        "values_tags": ["追求成长", "务实", "重视陪伴"],
        "lifestyle_tags": ["骑行", "篮球", "烹饪", "电影", "游戏"],
    },
    {
        "phone": "13900001005",
        "nickname": "刘子豪",
        "gender": Gender.MALE,
        "birth_date": datetime(1992, 8, 17),
        "city": "成都",
        "bio": "成都人，做建筑设计。平时喜欢打麻将、吃火锅，周末会去周边自驾游。性格随和，朋友都说我很好相处。四川男人，会做饭是基本技能。",
        "occupation": "建筑设计师",
        "education": "四川大学 本科",
        "height_cm": 173,
        "personality_tags": ["随和", "幽默", "顾家", "会享受生活"],
        "values_tags": ["家庭优先", "享受当下", "重视友情"],
        "lifestyle_tags": ["麻将", "火锅", "自驾", "摄影", "音乐"],
    },
    {
        "phone": "13900001006",
        "nickname": "赵俊杰",
        "gender": Gender.MALE,
        "birth_date": datetime(1990, 5, 2),
        "city": "广州",
        "bio": "在广州开了一家粤菜馆，虽然工作辛苦，但看着客人满意的笑容就很开心。想找一个能一起经营生活的人，最好也爱吃。",
        "occupation": "餐饮店主",
        "education": "华南理工大学 本科",
        "height_cm": 172,
        "personality_tags": ["勤劳", "实在", "顾家", "有手艺"],
        "values_tags": ["家庭优先", "务实", "追求品质生活"],
        "lifestyle_tags": ["烹饪", "跑步", "钓鱼", "看电影", "旅行"],
    },
    {
        "phone": "13900001007",
        "nickname": "周子墨",
        "gender": Gender.MALE,
        "birth_date": datetime(1996, 3, 8),
        "city": "武汉",
        "bio": "华科毕业，现在在光谷做芯片设计。虽然是理工男，但很浪漫，会写诗也会做饭。希望找到一个灵魂伴侣，一起看日出日落。",
        "occupation": "芯片设计工程师",
        "education": "华中科技大学 硕士",
        "height_cm": 177,
        "personality_tags": ["浪漫", "聪明", "有才华", "温柔"],
        "values_tags": ["追求精神共鸣", "重视感情", "有理想"],
        "lifestyle_tags": ["写诗", "烹饪", "羽毛球", "电影", "音乐"],
    },
    {
        "phone": "13900001008",
        "nickname": "孙浩然",
        "gender": Gender.MALE,
        "birth_date": datetime(1993, 12, 1),
        "city": "南京",
        "bio": "南大毕业，现在是一名心内科医生。工作虽然忙，但周末会去玄武湖跑步或者和朋友聚餐。希望能找一个理解医生工作的人。",
        "occupation": "心内科医生",
        "education": "南京大学 硕士",
        "height_cm": 179,
        "personality_tags": ["稳重", "有责任心", "善良", "专业"],
        "values_tags": ["事业心强", "家庭优先", "重视健康"],
        "lifestyle_tags": ["跑步", "篮球", "阅读", "美食", "旅行"],
    },
    {
        "phone": "13900001009",
        "nickname": "林风",
        "gender": Gender.MALE,
        "birth_date": datetime(1997, 7, 7),
        "city": "厦门",
        "bio": "厦大毕业，做旅游自媒体博主。喜欢冲浪和潜水，经常在海边拍照。性格开朗，喜欢交朋友，也喜欢尝试新事物。粉丝叫我'厦门小哥哥'。",
        "occupation": "自媒体博主",
        "education": "厦门大学 本科",
        "height_cm": 181,
        "personality_tags": ["阳光", "冒险", "有趣", "自由"],
        "values_tags": ["追求自由", "享受当下", "热爱生活"],
        "lifestyle_tags": ["冲浪", "潜水", "摄影", "旅行", "美食"],
    },
    {
        "phone": "13900001010",
        "nickname": "何峰",
        "gender": Gender.MALE,
        "birth_date": datetime(1994, 9, 30),
        "city": "长沙",
        "bio": "湖南卫视编导，工作很有趣但也很忙。喜欢看电影和话剧，自己也会写剧本。希望能找到一个能聊得来的人，一起讨论人生和艺术。",
        "occupation": "电视编导",
        "education": "湖南大学 本科",
        "height_cm": 174,
        "personality_tags": ["有趣", "有才华", "浪漫", "健谈"],
        "values_tags": ["追求精神生活", "重视沟通", "有理想"],
        "lifestyle_tags": ["电影", "话剧", "写作", "美食", "旅行"],
    },
    {
        "phone": "13900001011",
        "nickname": "吴嘉伟",
        "gender": Gender.MALE,
        "birth_date": datetime(1995, 11, 8),
        "city": "上海",
        "bio": "金融行业分析师，工作在陆家嘴。外表看起来很严肃，其实私下是个二次元爱好者。喜欢看动漫也喜欢打游戏，希望找到能理解我这份'反差萌'的人。",
        "occupation": "金融分析师",
        "education": "上海财经大学 硕士",
        "height_cm": 177,
        "personality_tags": ["理性", "内敛", "有趣", "细腻"],
        "values_tags": ["事业心强", "追求品质生活", "重视内心世界"],
        "lifestyle_tags": ["动漫", "游戏", "健身", "阅读", "咖啡"],
    },
    {
        "phone": "13900001012",
        "nickname": "郑凯",
        "gender": Gender.MALE,
        "birth_date": datetime(1992, 6, 15),
        "city": "北京",
        "bio": "互联网公司产品经理，周末喜欢烘焙和看展，性格温柔体贴。虽然是北方人，但骨子里很细腻。会做饭，会修家电，是朋友们口中的'暖男'。",
        "occupation": "产品经理",
        "education": "北京理工大学 本科",
        "height_cm": 175,
        "personality_tags": ["温柔", "体贴", "细心", "暖男"],
        "values_tags": ["家庭优先", "重视感情", "追求品质生活"],
        "lifestyle_tags": ["烘焙", "看展", "烹饪", "健身", "电影"],
    },
    {
        "phone": "13900001013",
        "nickname": "黄博文",
        "gender": Gender.MALE,
        "birth_date": datetime(1996, 1, 20),
        "city": "深圳",
        "bio": "腾讯后端开发工程师，码农中的文艺青年。平时写代码，周末写小说。已经在网上连载了两本科幻小说，希望找到一个爱看书的女生。",
        "occupation": "后端工程师",
        "education": "哈尔滨工业大学 本科",
        "height_cm": 174,
        "personality_tags": ["内敛", "有才华", "认真", "浪漫"],
        "values_tags": ["追求精神生活", "重视内在", "有理想"],
        "lifestyle_tags": ["写作", "阅读", "编程", "电影", "散步"],
    },
    {
        "phone": "13900001014",
        "nickname": "马晓东",
        "gender": Gender.MALE,
        "birth_date": datetime(1991, 10, 5),
        "city": "成都",
        "bio": "医学博士在读，热爱科研也热爱生活，希望找到理解我的人。平时泡实验室，周末会去爬青城山或者去宽窄巷子喝茶。四川人的快乐你懂的。",
        "occupation": "医学博士在读",
        "education": "四川大学 博士",
        "height_cm": 176,
        "personality_tags": ["认真", "踏实", "有追求", "温暖"],
        "values_tags": ["追求成长", "重视健康", "家庭优先"],
        "lifestyle_tags": ["科研", "爬山", "喝茶", "阅读", "散步"],
    },
    {
        "phone": "13900001015",
        "nickname": "杨帆",
        "gender": Gender.MALE,
        "birth_date": datetime(1994, 3, 12),
        "city": "杭州",
        "bio": "网易游戏策划，每天和游戏打交道。性格开朗，喜欢户外运动。周末要么在西湖边跑步，要么和朋友去千岛湖露营。希望你也喜欢大自然。",
        "occupation": "游戏策划",
        "education": "中国美术学院 本科",
        "height_cm": 178,
        "personality_tags": ["开朗", "有创意", "活力充沛", "随和"],
        "values_tags": ["享受当下", "追求自由", "重视体验"],
        "lifestyle_tags": ["游戏", "跑步", "露营", "摄影", "音乐"],
    },
]

FEMALE_USERS = [
    {
        "phone": "13900002001",
        "nickname": "林婉清",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1997, 3, 22),
        "city": "北京",
        "bio": "北大研究生毕业，现在是一名数据分析师。性格温柔但有主见，喜欢读书和听音乐，偶尔也会下厨做几道拿手菜。朋友圈里的'知心姐姐'。",
        "occupation": "数据分析师",
        "education": "北京大学 硕士",
        "height_cm": 165,
        "personality_tags": ["温柔", "独立", "聪明", "善解人意"],
        "values_tags": ["追求成长", "重视内心", "家庭优先"],
        "lifestyle_tags": ["读书", "音乐", "烹饪", "瑜伽", "电影"],
    },
    {
        "phone": "13900002002",
        "nickname": "陈雨薇",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1996, 7, 19),
        "city": "上海",
        "bio": "外企市场经理，喜欢健身和旅行。去过20多个国家，希望找到一个同样热爱探索世界的伴侣。性格开朗，喜欢交朋友。",
        "occupation": "市场经理",
        "education": "上海外国语大学 本科",
        "height_cm": 168,
        "personality_tags": ["开朗", "独立", "国际化", "有活力"],
        "values_tags": ["追求自由", "重视体验", "事业心强"],
        "lifestyle_tags": ["旅行", "健身", "美食", "跳舞", "外语"],
    },
    {
        "phone": "13900002003",
        "nickname": "苏小鱼",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1998, 9, 3),
        "city": "深圳",
        "bio": "腾讯UI设计师，喜欢画画和手工。养了一只叫'奶茶'的猫，周末会去逛展览或者宅在家追剧。希望找一个温柔体贴、喜欢小动物的人。",
        "occupation": "UI设计师",
        "education": "广州美术学院 本科",
        "height_cm": 162,
        "personality_tags": ["文艺", "温柔", "有爱心", "可爱"],
        "values_tags": ["重视感情", "追求美好", "享受当下"],
        "lifestyle_tags": ["画画", "手工", "撸猫", "展览", "追剧"],
    },
    {
        "phone": "13900002004",
        "nickname": "孙美琪",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1995, 12, 25),
        "city": "杭州",
        "bio": "浙大博士在读，研究人工智能方向。虽然是理工科女生，但内心很细腻，喜欢小动物和花草。希望能找到一个理解和支持我学业的人。",
        "occupation": "博士在读",
        "education": "浙江大学 博士",
        "height_cm": 163,
        "personality_tags": ["聪明", "认真", "细腻", "有追求"],
        "values_tags": ["追求成长", "重视知识", "独立自主"],
        "lifestyle_tags": ["科研", "小动物", "花草", "散步", "电影"],
    },
    {
        "phone": "13900002005",
        "nickname": "刘欣怡",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1997, 1, 9),
        "city": "成都",
        "bio": "小学语文老师，性格活泼开朗。喜欢和小朋友们在一起，也喜欢旅行和美食。周末会去逛街或者和闺蜜喝下午茶。成都女孩，爱吃辣。",
        "occupation": "小学教师",
        "education": "四川师范大学 本科",
        "height_cm": 160,
        "personality_tags": ["活泼", "开朗", "有爱心", "简单"],
        "values_tags": ["家庭优先", "重视感情", "享受当下"],
        "lifestyle_tags": ["旅行", "美食", "逛街", "看书", "唱歌"],
    },
    {
        "phone": "13900002006",
        "nickname": "王海伦",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1994, 10, 11),
        "city": "广州",
        "bio": "外企翻译，精通英语和法语。喜欢古典音乐和芭蕾舞，也会弹钢琴。性格比较安静，但内心很丰富。希望能遇到一个有品味的人。",
        "occupation": "翻译",
        "education": "广东外语外贸大学 硕士",
        "height_cm": 166,
        "personality_tags": ["优雅", "安静", "有内涵", "浪漫"],
        "values_tags": ["追求品质生活", "重视精神世界", "有品味"],
        "lifestyle_tags": ["古典音乐", "芭蕾", "钢琴", "阅读", "法语"],
    },
    {
        "phone": "13900002007",
        "nickname": "黄静怡",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1999, 6, 20),
        "city": "武汉",
        "bio": "武大法学研究生在读，梦想成为一名律师。平时喜欢辩论和演讲，也会弹吉他唱歌。看起来很文静，其实很有想法。独立女性就该有自己的态度。",
        "occupation": "研究生在读",
        "education": "武汉大学 硕士",
        "height_cm": 164,
        "personality_tags": ["有主见", "文静", "有才华", "有梦想"],
        "values_tags": ["追求成长", "独立自主", "重视公平"],
        "lifestyle_tags": ["辩论", "演讲", "吉他", "唱歌", "读书"],
    },
    {
        "phone": "13900002008",
        "nickname": "唐糖",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1996, 8, 14),
        "city": "南京",
        "bio": "幼儿园老师，超级喜欢小朋友。性格很温柔，朋友都说我是'治愈系'。喜欢画画、做手工，也喜欢小动物。希望找一个温暖的人一起过小日子。",
        "occupation": "幼儿园教师",
        "education": "南京师范大学 本科",
        "height_cm": 161,
        "personality_tags": ["温柔", "治愈", "有爱心", "简单"],
        "values_tags": ["家庭优先", "享受当下", "重视温暖"],
        "lifestyle_tags": ["画画", "手工", "小动物", "烘焙", "散步"],
    },
    {
        "phone": "13900002009",
        "nickname": "杨小幂",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1995, 4, 18),
        "city": "厦门",
        "bio": "在一家精品咖啡馆做店长，同时也是一个认证咖啡师。喜欢研究各种咖啡豆，也会拉花。性格独立但也很期待爱情。你可以不爱咖啡，但要爱我。",
        "occupation": "咖啡馆店长",
        "education": "华侨大学 本科",
        "height_cm": 167,
        "personality_tags": ["独立", "有品味", "温柔", "文艺"],
        "values_tags": ["追求品质生活", "独立自主", "享受当下"],
        "lifestyle_tags": ["咖啡", "烘焙", "阅读", "海边散步", "旅行"],
    },
    {
        "phone": "13900002010",
        "nickname": "赵雪莲",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1993, 11, 22),
        "city": "长沙",
        "bio": "三甲医院护士，工作虽然辛苦但很有成就感。性格温柔细心，很会照顾人。平时喜欢跳广场舞和养生。希望找一个踏实靠谱的人。",
        "occupation": "护士",
        "education": "中南大学 本科",
        "height_cm": 162,
        "personality_tags": ["温柔", "细心", "有爱心", "顾家"],
        "values_tags": ["家庭优先", "重视健康", "务实"],
        "lifestyle_tags": ["跳舞", "养生", "做饭", "看电影", "逛街"],
    },
    {
        "phone": "13900002011",
        "nickname": "周晓月",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1997, 5, 15),
        "city": "上海",
        "bio": "互联网公司运营经理，白天忙工作，晚上忙追剧。性格大大咧咧，朋友们都说我是'开心果'。喜欢美食，尤其喜欢探店。希望能找个一起吃遍全城的人。",
        "occupation": "运营经理",
        "education": "华东师范大学 本科",
        "height_cm": 163,
        "personality_tags": ["开朗", "大方", "有趣", "吃货"],
        "values_tags": ["享受当下", "重视友情", "追求快乐"],
        "lifestyle_tags": ["美食", "追剧", "逛街", "旅行", "瑜伽"],
    },
    {
        "phone": "13900002012",
        "nickname": "郑雨桐",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1996, 9, 8),
        "city": "北京",
        "bio": "自由插画师，给很多杂志和品牌画过插画。喜欢手帐和水彩，家里养了两只猫。性格有点社恐，但熟悉之后很话多。希望你也是一个有趣的人。",
        "occupation": "自由插画师",
        "education": "中央美术学院 本科",
        "height_cm": 166,
        "personality_tags": ["文艺", "安静", "有才华", "社恐"],
        "values_tags": ["追求自由", "重视内心世界", "有创意"],
        "lifestyle_tags": ["画画", "手帐", "撸猫", "咖啡", "电影"],
    },
    {
        "phone": "13900002013",
        "nickname": "许思琪",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1998, 2, 28),
        "city": "深圳",
        "bio": "跨境电商创业者，95后女老板。白天忙选品和直播，晚上喜欢去深圳湾跑步。独立是我的标签，但偶尔也想有人依靠。事业和爱情我都要。",
        "occupation": "电商创业者",
        "education": "暨南大学 本科",
        "height_cm": 167,
        "personality_tags": ["独立", "有野心", "活力充沛", "果断"],
        "values_tags": ["事业心强", "追求自由", "独立自主"],
        "lifestyle_tags": ["跑步", "直播", "旅行", "健身", "美食"],
    },
    {
        "phone": "13900002014",
        "nickname": "何佳怡",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1995, 7, 3),
        "city": "杭州",
        "bio": "互联网公司HR，见过太多人了，所以对自己的另一半也有更清晰的画像。性格温和，做事有条理。喜欢瑜伽和茶道，周末也会去西湖边走走。",
        "occupation": "HR经理",
        "education": "浙江工商大学 硕士",
        "height_cm": 164,
        "personality_tags": ["温和", "有条理", "善解人意", "稳重"],
        "values_tags": ["追求平衡", "重视内在", "家庭优先"],
        "lifestyle_tags": ["瑜伽", "茶道", "散步", "阅读", "烹饪"],
    },
    {
        "phone": "13900002015",
        "nickname": "冯诗涵",
        "gender": Gender.FEMALE,
        "birth_date": datetime(1994, 12, 10),
        "city": "成都",
        "bio": "火锅店合伙人+美食博主，成都土著。对火锅的热爱深入骨髓，对生活的热爱同样如此。性格豪爽大方，典型的川妹子。找个能吃辣的另一半。",
        "occupation": "餐饮合伙人 / 美食博主",
        "education": "西南财经大学 本科",
        "height_cm": 165,
        "personality_tags": ["豪爽", "大方", "热情", "吃货"],
        "values_tags": ["享受当下", "重视友情", "追求快乐"],
        "lifestyle_tags": ["美食", "火锅", "旅行", "摄影", "直播"],
    },
]


# ============================================================
# Match Records
# ============================================================
MATCH_RECORDS = [
    # (male_idx, female_idx, compatibility, voice, face, personality, values, health, lifestyle, status_a, status_b, is_mutual)
    (0, 0, 87.5, 82.0, 85.0, 90.0, 88.0, 80.0, 86.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (1, 1, 85.2, 80.0, 83.0, 88.0, 86.0, 78.0, 90.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (2, 2, 82.3, 78.0, 80.0, 85.0, 82.0, 76.0, 88.0, MatchStatus.ACCEPTED, MatchStatus.PENDING, False),
    (3, 3, 91.0, 88.0, 90.0, 92.0, 93.0, 85.0, 89.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (4, 4, 79.8, 75.0, 78.0, 82.0, 80.0, 72.0, 85.0, MatchStatus.PENDING, MatchStatus.PENDING, False),
    (5, 5, 76.5, 72.0, 74.0, 78.0, 77.0, 70.0, 80.0, MatchStatus.ACCEPTED, MatchStatus.PENDING, False),
    (6, 6, 88.3, 85.0, 87.0, 89.0, 90.0, 82.0, 86.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (7, 7, 83.7, 80.0, 82.0, 86.0, 84.0, 79.0, 85.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (8, 8, 80.1, 76.0, 79.0, 82.0, 81.0, 74.0, 87.0, MatchStatus.PENDING, MatchStatus.ACCEPTED, False),
    (9, 9, 77.4, 73.0, 75.0, 80.0, 78.0, 71.0, 82.0, MatchStatus.REJECTED, MatchStatus.PENDING, False),
    (10, 10, 84.6, 81.0, 83.0, 87.0, 85.0, 80.0, 86.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (11, 11, 86.9, 83.0, 85.0, 90.0, 87.0, 81.0, 88.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (12, 12, 78.2, 74.0, 76.0, 81.0, 79.0, 73.0, 83.0, MatchStatus.PENDING, MatchStatus.PENDING, False),
    (13, 13, 89.1, 86.0, 88.0, 91.0, 90.0, 83.0, 87.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (14, 14, 81.5, 77.0, 80.0, 84.0, 82.0, 75.0, 86.0, MatchStatus.ACCEPTED, MatchStatus.PENDING, False),
    # Cross-city matches
    (0, 1, 72.3, 68.0, 70.0, 75.0, 73.0, 65.0, 78.0, MatchStatus.PENDING, MatchStatus.PENDING, False),
    (3, 6, 85.8, 82.0, 84.0, 88.0, 86.0, 79.0, 87.0, MatchStatus.ACCEPTED, MatchStatus.PENDING, False),
    (7, 10, 74.6, 70.0, 72.0, 77.0, 75.0, 68.0, 80.0, MatchStatus.PENDING, MatchStatus.REJECTED, False),
    (11, 12, 83.4, 79.0, 82.0, 86.0, 84.0, 77.0, 85.0, MatchStatus.ACCEPTED, MatchStatus.ACCEPTED, True),
    (14, 4, 70.9, 66.0, 69.0, 73.0, 71.0, 64.0, 76.0, MatchStatus.PENDING, MatchStatus.PENDING, False),
]


# ============================================================
# Conversation Threads (10 threads with messages)
# ============================================================
CONVERSATIONS = [
    # (match_idx, [(sender_is_a, content, minutes_ago), ...])
    (0, [
        (True, "你好呀，看到你也喜欢旅行和摄影，好巧！", 120),
        (False, "是呀！你都去过哪些地方？", 115),
        (True, "去过日本、泰国、新西兰，最喜欢新西兰的星空。你呢？", 110),
        (False, "哇，新西兰！我一直想去。我去年去了冰岛，极光超美的！", 105),
        (True, "冰岛也在我的清单上！下次可以一起规划一次旅行？", 100),
        (False, "好呀好呀，期待！😊", 95),
    ]),
    (1, [
        (True, "你好，看到你也是做互联网的，认识一下？", 200),
        (False, "好呀，你做哪个方向？", 195),
        (True, "我是AI方向的CTO，主要做NLP相关的产品。你做数据分析？", 190),
        (False, "对，主要做用户增长方向的数据分析。AI好厉害，能教教我吗？", 185),
        (True, "当然可以，改天请你喝咖啡慢慢聊？", 180),
        (False, "可以呀，周末有空吗？", 175),
    ]),
    (3, [
        (True, "你好美琪，看到你也是浙大的，我是隔壁阿里的。", 300),
        (False, "哈哈，浙大帮！你好呀~", 295),
        (True, "你在研究什么方向？我记得浙大AI很强。", 290),
        (False, "我在做计算机视觉方向，主要研究图像生成。", 285),
        (True, "太巧了，我们团队最近也在做AIGC相关的项目！", 280),
        (False, "那我们有很多共同话题呢。", 275),
        (True, "周末一起吃个饭聊聊？我知道一家很好的杭帮菜。", 270),
        (False, "好呀，我喜欢杭帮菜！", 265),
    ]),
    (6, [
        (True, "你好静静，看到你喜欢辩论和吉他，好有才华！", 400),
        (False, "谢谢！你对芯片设计感兴趣吗？", 395),
        (True, "说实话我更对会弹吉他的人感兴趣😄", 390),
        (False, "哈哈哈，那我可以弹给你听~", 385),
    ]),
    (7, [
        (True, "你好糖糖，医生配幼师，感觉很搭呢。", 500),
        (False, "哈哈，为什么这么说？", 495),
        (True, "都是照顾人的职业呀，只是对象不同而已。", 490),
        (False, "说得很有道理呢！你平时忙吗？", 485),
        (True, "确实比较忙，但周末一般会有空。你呢？", 480),
        (False, "我周末一般会去画画或者做手工，可以一起呀~", 475),
    ]),
    (10, [
        (True, "晓月你好，看到你也是互联网的，握个爪！", 600),
        (False, "哈哈，互联网打工人！", 595),
        (True, "你在哪个公司？做什么方向？", 590),
        (False, "我在一家电商平台做运营，你呢？", 585),
        (True, "金融分析，陆家嘴打工人。改天请你吃个饭？", 580),
        (False, "好呀，我知道陆家嘴有家不错的日料。", 575),
    ]),
    (11, [
        (True, "雨桐你好，看到你是插画师，太酷了！", 700),
        (False, "谢谢~ 你是做什么的？", 695),
        (True, "我做产品经理的，平时也喜欢看展和烘焙。", 690),
        (False, "烘焙！我也喜欢！你一般做什么？", 685),
        (True, "戚风蛋糕和提拉米苏是我的拿手戏，改天做给你尝尝？", 680),
        (False, "好期待！那我送你一幅画当回礼~", 675),
    ]),
    (13, [
        (True, "佳怡你好，HR看人很准吧？我是什么类型的？", 800),
        (False, "哈哈，你简历上写的'踏实稳重有追求'，我觉得挺准的。", 795),
        (True, "那你呢？HR的择偶标准是不是特别高？", 790),
        (False, "还好啦，主要是看感觉和三观。你平时喜欢做什么？", 785),
        (True, "写诗、做饭、看电影。比较宅但也很浪漫。", 780),
        (False, "理工男还会写诗？好有反差感！", 775),
        (True, "改天写一首送你？", 770),
        (False, "好呀，期待~ 🌸", 765),
    ]),
    (18, [
        (True, "诗涵你好，看到你是美食博主，我也是个吃货！", 900),
        (False, "那太好了！你最能吃辣吗？", 895),
        (True, "额...微辣可以接受，中辣可能要哭了😂", 890),
        (False, "没关系，我可以慢慢培养你！从鸳鸯锅开始~", 885),
    ]),
    (5, [
        (True, "海伦你好，看到你会弹钢琴，好优雅！", 1000),
        (False, "谢谢，你也喜欢音乐吗？", 995),
        (True, "我喜欢钓鱼和跑步，可能不太文艺哈哈。", 990),
        (False, "没关系呀，运动也很好。踏实的人很有魅力。", 985),
    ]),
]


# ============================================================
# Health Reports (5 reports)
# ============================================================
HEALTH_REPORTS = [
    # user_idx (male), overall_score, voice, face, personality, lifestyle, values, suggestions
    (0, 85.2, {
        "tone": "温暖有力",
        "clarity": 88,
        "emotion_stability": 82,
        "attractiveness": 85,
        "summary": "声音温暖有磁性，语速适中，表达清晰。"
    }, {
        "symmetry": 92,
        "skin_quality": 85,
        "expression_naturalness": 88,
        "attractiveness": 86,
        "summary": "面部对称性好，表情自然，亲和力强。"
    }, {
        "openness": 85,
        "conscientiousness": 88,
        "extraversion": 82,
        "agreeableness": 90,
        "neuroticism": 25,
        "summary": "性格开朗乐观，责任心强，情绪稳定。"
    }, {
        "exercise_frequency": 80,
        "sleep_quality": 75,
        "social_activity": 85,
        "summary": "运动频率适中，社交活跃度高。"
    }, {
        "family_oriented": 88,
        "career_ambition": 85,
        "life_quality": 90,
        "summary": "注重生活品质，事业心与家庭观平衡良好。"
    }, ["建议增加运动频率以提升整体健康分数", "可以尝试更多社交活动拓展人脉", "保持积极乐观的心态"]),
    (3, 92.1, {
        "tone": "清晰自信",
        "clarity": 90,
        "emotion_stability": 88,
        "attractiveness": 87,
        "summary": "声音清晰自信，逻辑性强，表达流畅。"
    }, {
        "symmetry": 90,
        "skin_quality": 88,
        "expression_naturalness": 85,
        "attractiveness": 84,
        "summary": "面部线条分明，气质沉稳。"
    }, {
        "openness": 88,
        "conscientiousness": 92,
        "extraversion": 75,
        "agreeableness": 85,
        "neuroticism": 20,
        "summary": "高度自律，理性思考，情绪非常稳定。"
    }, {
        "exercise_frequency": 85,
        "sleep_quality": 70,
        "social_activity": 72,
        "summary": "运动频率高，但睡眠质量有待提升。"
    }, {
        "family_oriented": 80,
        "career_ambition": 95,
        "life_quality": 85,
        "summary": "事业心极强，需要平衡工作与生活。"
    }, ["建议改善睡眠质量，避免熬夜", "在追求事业的同时注意平衡感情生活", "可以培养更多休闲爱好"]),
    (7, 88.5, {
        "tone": "温和专业",
        "clarity": 92,
        "emotion_stability": 85,
        "attractiveness": 83,
        "summary": "声音温和专业，给人安全感和信任感。"
    }, {
        "symmetry": 88,
        "skin_quality": 82,
        "expression_naturalness": 90,
        "attractiveness": 82,
        "summary": "表情自然亲切，有医生的专业气质。"
    }, {
        "openness": 80,
        "conscientiousness": 95,
        "extraversion": 70,
        "agreeableness": 92,
        "neuroticism": 22,
        "summary": "极度负责，善良温和，专业素养高。"
    }, {
        "exercise_frequency": 78,
        "sleep_quality": 65,
        "social_activity": 68,
        "summary": "受工作影响睡眠质量偏低，社交活动较少。"
    }, {
        "family_oriented": 90,
        "career_ambition": 82,
        "life_quality": 80,
        "summary": "家庭观念强，但在工作与生活平衡上需要改善。"
    }, ["建议增加休息时间，注意身体健康", "可以安排更多社交活动", "工作之余要学会放松自己"]),
    (11, 86.7, {
        "tone": "温柔细腻",
        "clarity": 85,
        "emotion_stability": 80,
        "attractiveness": 86,
        "summary": "声音温柔，表达细腻，给人温暖的感觉。"
    }, {
        "symmetry": 86,
        "skin_quality": 84,
        "expression_naturalness": 88,
        "attractiveness": 85,
        "summary": "五官端正，笑容温暖，亲和力强。"
    }, {
        "openness": 85,
        "conscientiousness": 88,
        "extraversion": 78,
        "agreeableness": 92,
        "neuroticism": 28,
        "summary": "体贴细心，善于照顾他人感受。"
    }, {
        "exercise_frequency": 82,
        "sleep_quality": 80,
        "social_activity": 75,
        "summary": "生活习惯健康，作息规律。"
    }, {
        "family_oriented": 92,
        "career_ambition": 75,
        "life_quality": 88,
        "summary": "重视家庭和生活品质，是理想的伴侣类型。"
    }, ["保持现有的健康生活方式", "可以适当提升社交圈", "建议培养更多个人爱好"]),
    (13, 83.4, {
        "tone": "沉稳内敛",
        "clarity": 82,
        "emotion_stability": 78,
        "attractiveness": 80,
        "summary": "声音沉稳，说话有条理，但语速偏慢。"
    }, {
        "symmetry": 85,
        "skin_quality": 80,
        "expression_naturalness": 75,
        "attractiveness": 79,
        "summary": "面部表情较少，需要练习微笑。"
    }, {
        "openness": 88,
        "conscientiousness": 90,
        "extraversion": 60,
        "agreeableness": 85,
        "neuroticism": 30,
        "summary": "内在丰富，但外向性偏低，需增加社交主动性。"
    }, {
        "exercise_frequency": 65,
        "sleep_quality": 72,
        "social_activity": 55,
        "summary": "运动和社交频率偏低，建议增加户外活动。"
    }, {
        "family_oriented": 85,
        "career_ambition": 80,
        "life_quality": 78,
        "summary": "内在追求高，但外在表达需要加强。"
    }, ["建议增加运动和社交活动", "在相亲时多微笑，展现亲和力", "可以学习一些社交技巧", "保持真诚和耐心"]),
]


# ============================================================
# Subscription Records (3)
# ============================================================
SUBSCRIPTION_RECORDS = [
    # user_idx, tier, days_ago_started, days_until_expiry, amount, payment_id
    (0, SubscriptionTier.VIP, 15, 45, 299.0, "PAY_WX_20260401001"),
    (3, SubscriptionTier.SVIP, 30, 60, 599.0, "PAY_WX_20260301002"),
    (11, SubscriptionTier.BASIC, 7, 23, 99.0, "PAY_ZFB_20260421003"),
]


# ============================================================
# Main Seed Function
# ============================================================
async def seed_database(reset: bool = False):
    """Seed the database with comprehensive demo data."""
    print("=" * 60)
    print("  Minder AI红娘 - 演示数据生成")
    print("=" * 60)
    print()

    if reset:
        print("[0/6] 重置数据库 (删除并重建所有表)...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ 数据库已重置")
    else:
        print("[0/6] 初始化数据库表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ 数据库表就绪")

    async with async_session() as db:
        try:
            # --- Users ---
            print()
            print("[1/6] 创建用户 (30人)...")
            all_users = []
            all_data = MALE_USERS + FEMALE_USERS

            for i, udata in enumerate(all_data):
                # Check if phone exists
                from sqlalchemy import select
                existing = await db.execute(
                    select(User).where(User.phone == udata["phone"])
                )
                if existing.scalar_one_or_none():
                    print(f"  ⚠ 用户 {udata['nickname']} 已存在，跳过")
                    # Fetch existing
                    res = await db.execute(select(User).where(User.phone == udata["phone"]))
                    all_users.append(res.scalar_one())
                    continue

                user = User(
                    phone=udata["phone"],
                    password_hash=DEMO_PASSWORD_HASH,
                    nickname=udata["nickname"],
                    gender=udata["gender"],
                    birth_date=udata["birth_date"],
                    city=udata["city"],
                    bio=udata["bio"],
                    occupation=udata["occupation"],
                    education=udata["education"],
                    height_cm=udata["height_cm"],
                    avatar_url=f"/static/avatars/demo_{i+1}.jpg",
                    is_active=True,
                    is_verified=True,
                    preferred_gender=Gender.FEMALE if udata["gender"] == Gender.MALE else Gender.MALE,
                    preferred_age_min=22,
                    preferred_age_max=35,
                    preferred_city=udata["city"],
                    personality_tags=udata["personality_tags"],
                    values_tags=udata["values_tags"],
                    lifestyle_tags=udata["lifestyle_tags"],
                    health_score=round(random.uniform(70, 95), 1),
                    personality_vector=[round(random.uniform(0, 1), 3) for _ in range(16)],
                    values_vector=[round(random.uniform(0, 1), 3) for _ in range(16)],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                )
                db.add(user)
                await db.flush()
                all_users.append(user)

                gender_icon = "♂" if udata["gender"] == Gender.MALE else "♀"
                print(f"  ✓ [{i+1:2d}/30] {udata['nickname']} ({udata['city']}) {gender_icon} - {udata['occupation']}")

            await db.commit()
            print(f"  → 共创建/加载 {len(all_users)} 个用户")

            # --- Matches ---
            print()
            print("[2/6] 创建匹配记录 (20条)...")
            all_matches = []
            num_males = len(MALE_USERS)
            for i, (ma_idx, fe_idx, comp, voice, face, pers, vals, health, life, sa, sb, mutual) in enumerate(MATCH_RECORDS):
                # fe_idx is relative to FEMALE_USERS, offset into all_users
                fe_user_idx = num_males + fe_idx
                # Check for existing match
                existing_match = await db.execute(
                    select(Match).where(
                        Match.user_a_id == all_users[ma_idx].id,
                        Match.user_b_id == all_users[fe_user_idx].id,
                    )
                )
                existing_match = existing_match.scalar_one_or_none()
                if existing_match:
                    all_matches.append(existing_match)
                    ma_name = all_users[ma_idx].nickname
                    fe_name = all_users[fe_user_idx].nickname
                    print(f"  ⚠ [{i+1:2d}/20] {ma_name} ↔ {fe_name} 已存在，跳过")
                    continue

                match = Match(
                    user_a_id=all_users[ma_idx].id,
                    user_b_id=all_users[fe_user_idx].id,
                    compatibility_score=comp,
                    voice_score=voice,
                    face_score=face,
                    personality_score=pers,
                    values_score=vals,
                    health_score=health,
                    lifestyle_score=life,
                    status_a=sa,
                    status_b=sb,
                    is_mutual=mutual,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                )
                db.add(match)
                await db.flush()
                all_matches.append(match)

                ma_name = all_users[ma_idx].nickname
                fe_name = all_users[fe_user_idx].nickname
                status_str = "互相匹配✓" if mutual else f"{sa.value}/{sb.value}"
                print(f"  ✓ [{i+1:2d}/20] {ma_name} ↔ {fe_name}  分数:{comp}  状态:{status_str}")

            await db.commit()

            # --- Messages ---
            print()
            print("[3/6] 创建对话和消息 (10个线程)...")
            msg_count = 0
            for conv_idx, (match_idx, messages) in enumerate(CONVERSATIONS):
                match = all_matches[match_idx]
                for sender_is_a, content, minutes_ago in messages:
                    sender_id = match.user_a_id if sender_is_a else match.user_b_id
                    msg = Message(
                        match_id=match.id,
                        sender_id=sender_id,
                        content=content,
                        message_type="text",
                        is_read=random.choice([True, True, True, False]),
                        created_at=datetime.utcnow() - timedelta(minutes=minutes_ago),
                    )
                    db.add(msg)
                    msg_count += 1

                ma_name = all_users[0].nickname  # placeholder
                # Get actual names from match
                from sqlalchemy import select as sel
                ua = await db.execute(sel(User).where(User.id == match.user_a_id))
                ub = await db.execute(sel(User).where(User.id == match.user_b_id))
                ua_name = ua.scalar_one().nickname
                ub_name = ub.scalar_one().nickname
                print(f"  ✓ 对话{conv_idx+1}: {ua_name} ↔ {ub_name} ({len(messages)}条消息)")

            await db.commit()
            print(f"  → 共创建 {msg_count} 条消息")

            # --- Health Reports ---
            print()
            print("[4/6] 创建健康报告 (5份)...")
            for user_idx, overall, voice_a, face_a, pers_a, life_a, vals_a, suggestions in HEALTH_REPORTS:
                report = HealthReport(
                    user_id=all_users[user_idx].id,
                    overall_score=overall,
                    voice_analysis=voice_a,
                    face_analysis=face_a,
                    personality_analysis=pers_a,
                    lifestyle_analysis=life_a,
                    values_analysis=vals_a,
                    suggestions=suggestions,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
                )
                db.add(report)
                uname = all_users[user_idx].nickname
                print(f"  ✓ {uname} - 健康分数: {overall}")

            await db.commit()

            # --- Subscriptions ---
            print()
            print("[5/6] 创建订阅记录 (3条)...")
            for user_idx, tier, days_ago, days_left, amount, pay_id in SUBSCRIPTION_RECORDS:
                started = datetime.utcnow() - timedelta(days=days_ago)
                expires = datetime.utcnow() + timedelta(days=days_left)
                sub = Subscription(
                    user_id=all_users[user_idx].id,
                    tier=tier,
                    started_at=started,
                    expires_at=expires,
                    is_active=True,
                    payment_id=pay_id,
                    amount=amount,
                )
                db.add(sub)
                uname = all_users[user_idx].nickname
                print(f"  ✓ {uname} - {tier.value}  ¥{amount}  有效至 {expires.strftime('%Y-%m-%d')}")

            # Update user subscription tiers
            all_users[0].subscription_tier = SubscriptionTier.VIP
            all_users[0].subscription_expires_at = datetime.utcnow() + timedelta(days=45)
            all_users[3].subscription_tier = SubscriptionTier.SVIP
            all_users[3].subscription_expires_at = datetime.utcnow() + timedelta(days=60)
            all_users[11].subscription_tier = SubscriptionTier.BASIC
            all_users[11].subscription_expires_at = datetime.utcnow() + timedelta(days=23)

            await db.commit()

            # --- Summary ---
            print()
            print("[6/6] 统计汇总...")
            from sqlalchemy import func, select as sel2
            user_count = (await db.execute(sel2(func.count(User.id)))).scalar()
            match_count = (await db.execute(sel2(func.count(Match.id)))).scalar()
            msg_count_res = (await db.execute(sel2(func.count(Message.id)))).scalar()
            report_count = (await db.execute(sel2(func.count(HealthReport.id)))).scalar()
            sub_count = (await db.execute(sel2(func.count(Subscription.id)))).scalar()

            print(f"  用户: {user_count}")
            print(f"  匹配: {match_count}")
            print(f"  消息: {msg_count_res}")
            print(f"  健康报告: {report_count}")
            print(f"  订阅: {sub_count}")

        except Exception as e:
            await db.rollback()
            print(f"\n  ✗ 数据导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    print()
    print("=" * 60)
    print("  演示数据生成完成！")
    print("=" * 60)
    print()
    print("测试账号 (所有密码: Demo123456!):")
    print("-" * 60)
    print(f"  {'手机号':<18} {'昵称':<12} {'城市':<8} {'职业':<20}")
    print("-" * 60)
    demo_users = MALE_USERS[:5] + FEMALE_USERS[:5]
    for u in demo_users:
        print(f"  {u['phone']:<18} {u['nickname']:<12} {u['city']:<8} {u['occupation']:<20}")
    print("-" * 60)
    print(f"  ... 共 {len(MALE_USERS) + len(FEMALE_USERS)} 个用户")
    print()
    print("运行服务: cd ~/Desktop/婚恋AI && python3 -m minder.main")
    print()

    return True


# ============================================================
# Entry Point
# ============================================================
def main():
    reset = "--reset" in sys.argv
    success = asyncio.run(seed_database(reset=reset))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

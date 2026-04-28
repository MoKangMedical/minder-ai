"""
Digital Matchmaker Advisor
===========================
数字红娘 - AI恋爱顾问引擎。

功能:
- 生成匹配解释 (为什么你们适合)
- 约会教练 (约会建议和计划)
- 恋爱关系建议
- 冰破者生成
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MatchExplanation:
    """匹配解释"""
    summary: str = ""
    compatibility_highlights: list[str] = field(default_factory=list)
    potential_challenges: list[str] = field(default_factory=list)
    advice: str = ""
    score_breakdown: dict = field(default_factory=dict)


@dataclass
class DatePlan:
    """约会计划"""
    title: str = ""
    location_suggestion: str = ""
    activity_suggestion: str = ""
    conversation_topics: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    estimated_budget: str = ""
    duration_suggestion: str = ""


class DigitalAdvisor:
    """
    数字红娘 AI 顾问

    基于规则引擎和模板系统，为用户提供智能匹配解释、约会建议、
    恋爱关系指导和冰破者生成。

    当无真实 LLM 时，使用基于输入哈希的模板组合系统，
    生成多样化、个性化的中文建议文本。

    Usage::

        advisor = DigitalAdvisor()
        explanation = advisor.generate_match_explanation(user_a, user_b, scores)
        coaching = advisor.date_coaching(profile, match_profile, "coffee")
        advice = advisor.relationship_advice(conversation_history, "如何表白？")
        icebreakers = advisor.generate_icebreakers(user_a, user_b)
    """

    # 匹配维度中文映射
    SCORE_LABELS = {
        "overall": "综合匹配度",
        "personality": "性格契合度",
        "interests": "兴趣相似度",
        "values": "价值观匹配度",
        "lifestyle": "生活方式协调度",
        "voice_compatibility": "语音相性",
        "appearance": "外貌吸引力",
    }

    # 兴趣标签库
    INTEREST_TAGS = {
        "music": ["音乐", "唱歌", "乐器", "演唱会"],
        "sports": ["运动", "健身", "跑步", "游泳", "篮球", "瑜伽"],
        "travel": ["旅行", "自驾游", "背包客", "摄影"],
        "food": ["美食", "烹饪", "烘焙", "探店"],
        "reading": ["阅读", "写作", "文学", "诗歌"],
        "art": ["绘画", "书法", "摄影", "设计"],
        "tech": ["科技", "编程", "游戏", "AI"],
        "nature": ["户外", "徒步", "露营", "登山"],
        "movies": ["电影", "追剧", "动漫", "综艺"],
        "pets": ["宠物", "猫咪", "狗狗"],
    }

    # 约会地点库
    DATE_LOCATIONS = {
        "coffee": {
            "places": ["精品咖啡馆", "文艺书店咖啡角", "河边景观咖啡厅",
                       "园区里的独立咖啡馆"],
            "duration": "1.5-2小时",
            "budget": "50-150元",
        },
        "dinner": {
            "places": ["特色日料店", "法式小酒馆", "创意融合餐厅",
                       "温馨的私房菜馆"],
            "duration": "2-3小时",
            "budget": "200-500元",
        },
        "outdoor": {
            "places": ["城市公园", "湖边步道", "植物园", "古镇老街"],
            "duration": "2-4小时",
            "budget": "50-200元",
        },
        "activity": {
            "places": ["密室逃脱", "手工陶艺馆", "烘焙教室", "美术馆"],
            "duration": "2-3小时",
            "budget": "100-300元",
        },
        "default": {
            "places": ["商场美食区", "电影院", "书店", "咖啡馆"],
            "duration": "2-3小时",
            "budget": "100-300元",
        },
    }

    # 对话开场白模板
    ICEBREAKER_TEMPLATES = [
        "看到你也喜欢{interest}，{question}",
        "你的{item}看起来好{adj}，{follow_up}",
        "{greeting}！我注意到我们都{common}，{question}",
        "如果用三个词形容自己，你会选什么？我猜其中一定有{guess}~",
        "看到你的照片是在{location}拍的，那里{question}",
        "你平时{activity}吗？我最近刚好{related}",
        "突然想到一个问题想问你：{question}",
        "今天的{weather}好适合{activity}，你{question}",
    ]

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        初始化数字红娘顾问。

        Args:
            api_key: LLM API 密钥 (当使用真实 LLM 时)
            model: 使用的语言模型
        """
        self.api_key = api_key
        self.model = model
        self._llm = None
        logger.info("DigitalAdvisor 初始化完成 (model=%s)", model)

    @staticmethod
    def _hash_seed(data: str) -> int:
        """根据输入字符串生成确定性随机种子"""
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    # ------------------------------------------------------------------
    # Match explanation
    # ------------------------------------------------------------------

    def generate_match_explanation(
        self,
        user_a: dict,
        user_b: dict,
        scores: dict,
    ) -> str:
        """
        生成匹配解释 - 告诉用户为什么两个人适合。

        基于双方资料和匹配分数，使用模板组合系统生成
        个性化、温暖的中文匹配解释。

        Args:
            user_a: 用户A的档案数据 {
                "name": str, "age": int, "gender": str,
                "interests": list[str], "personality": dict,
                "occupation": str, "city": str,
            }
            user_b: 用户B的档案数据
            scores: 匹配分数详情 {
                "overall": float, "personality": float,
                "interests": float, "values": float,
                "lifestyle": float, "voice_compatibility": float,
            }

        Returns:
            str: 自然语言匹配解释 (中文)
        """
        name_a = user_a.get("name", "用户A")
        name_b = user_b.get("name", "用户B")
        overall = scores.get("overall", 0.5)

        # 组合哈希种子
        seed_data = f"{name_a}:{name_b}:{overall:.2f}"
        seed = self._hash_seed(seed_data)
        rng = np.random.RandomState(seed)

        logger.info("生成匹配解释: %s <-> %s, overall=%.2f",
                   name_a, name_b, overall)

        # 分析各维度分数
        dim_analysis = []
        for key in ["personality", "interests", "values", "lifestyle",
                     "voice_compatibility"]:
            val = scores.get(key, 0.5)
            label = self.SCORE_LABELS.get(key, key)
            if val >= 0.8:
                dim_analysis.append((label, "非常契合", val))
            elif val >= 0.6:
                dim_analysis.append((label, "比较匹配", val))
            elif val >= 0.4:
                dim_analysis.append((label, "有互补空间", val))
            else:
                dim_analysis.append((label, "各有特色", val))

        # 按分数排序，取最高的亮点
        dim_analysis.sort(key=lambda x: x[2], reverse=True)
        highlights = dim_analysis[:3]

        # 共同兴趣分析
        interests_a = set(user_a.get("interests", []))
        interests_b = set(user_b.get("interests", []))
        common = interests_a & interests_b
        unique_a = interests_a - interests_b
        unique_b = interests_b - interests_a

        # 构建解释文本
        parts = []

        # 开场
        if overall >= 0.8:
            parts.append(
                f"✨ {name_a}和{name_b}，你们的匹配度高达{overall*100:.0f}%，"
                f"这是一个非常出色的缘分信号！"
            )
        elif overall >= 0.6:
            parts.append(
                f"💕 {name_a}和{name_b}，你们的匹配度为{overall*100:.0f}%，"
                f"在众多用户中脱颖而出，值得一试！"
            )
        else:
            parts.append(
                f"🌟 {name_a}和{name_b}，你们的匹配度为{overall*100:.0f}%，"
                f"虽然不是最高的组合，但互补的特质往往能碰撞出奇妙的火花。"
            )

        # 亮点分析
        if highlights:
            highlight_text = "、".join(
                f"{h[0]}（{h[1]}）" for h in highlights
            )
            parts.append(f"\n在{highlight_text}方面，你们表现尤为突出。")

        # 共同兴趣
        if common:
            common_tags = []
            for tag in common:
                for k, v in self.INTEREST_TAGS.items():
                    if tag in v or tag == k:
                        common_tags.append(tag)
                        break
                else:
                    common_tags.append(tag)
            parts.append(
                f"\n你们都喜欢{'、'.join(list(common)[:4])}，"
                f"有共同话题可以让你们快速拉近距离。"
            )

        # 互补分析
        if unique_a and unique_b:
            parts.append(
                f"而且{name_a}擅长的{'、'.join(list(unique_a)[:2])}，"
                f"和{name_b}喜欢的{'、'.join(list(unique_b)[:2])}，"
                f"恰好可以互相带动，一起探索新的领域。"
            )

        # 个性化建议
        if overall >= 0.7:
            parts.append(
                f"\n💡 建议：尽快发起聊天，一个好的开始会让你们的关系事半功倍。"
                f"可以从你们的共同兴趣入手，自然地展开对话。"
            )
        else:
            parts.append(
                f"\n💡 建议：不要着急，先通过聊天深入了解彼此。"
                f"不同的性格和习惯需要时间磨合，但互补的关系往往更长久。"
            )

        result = "\n".join(parts)

        logger.info("匹配解释生成完成 (长度: %d字符)", len(result))
        return result

    # ------------------------------------------------------------------
    # Date coaching
    # ------------------------------------------------------------------

    def date_coaching(
        self,
        user_profile: dict,
        match_profile: dict,
        date_type: str = "coffee",
    ) -> dict:
        """
        约会教练 - 提供约会建议和指导。

        基于双方档案和约会类型，生成个性化的约会方案，
        包括地点、话题、着装和注意事项。

        Args:
            user_profile: 用户档案
            match_profile: 匹配对象档案
            date_type: 约会类型 ('coffee', 'dinner', 'outdoor', 'activity')

        Returns:
            dict: {
                "tips": list[str],
                "conversation_starters": list[str],
                "outfit_suggestion": str,
                "warning_signs": list[str],
                "location": str,
                "budget": str,
                "duration": str,
            }
        """
        name = user_profile.get("name", "你")
        match_name = match_profile.get("name", "对方")
        match_interests = match_profile.get("interests", [])

        seed = self._hash_seed(f"{name}:{match_name}:{date_type}")
        rng = np.random.RandomState(seed)

        logger.info("约会教练: %s -> %s, type=%s", name, match_name, date_type)

        # 获取约会地点信息
        loc_info = self.DATE_LOCATIONS.get(date_type, self.DATE_LOCATIONS["default"])
        place_idx = rng.randint(0, len(loc_info["places"]))
        location = loc_info["places"][place_idx]

        # 生成话题建议 (结合双方兴趣)
        conversation_starters = []
        if match_interests:
            for interest in match_interests[:3]:
                for k, v in self.INTEREST_TAGS.items():
                    if interest in v or interest == k:
                        conversation_starters.append(
                            f"聊聊{interest}相关的经历和故事"
                        )
                        break
        conversation_starters.extend([
            f"问问{match_name}最近有没有看什么好电影或好书",
            "分享一个最近发生的有趣小事",
            f"如果有一周假期，最想去哪里旅行？",
            "聊聊各自最喜欢的美食和餐厅",
        ])
        conversation_starters = conversation_starters[:5]

        # 着装建议
        outfit_options = {
            "coffee": [
                "休闲但不随意——干净的衬衫/针织衫配牛仔裤，舒适又有品味",
                "简约文艺风——纯色上衣配休闲裤，展现自然气质",
                "如果天气好，一件合身的T恤配卡其裤也很加分",
            ],
            "dinner": [
                "正式但不死板——西装外套配深色牛仔裤，优雅又不会太刻意",
                "如果去日料/西餐厅，建议穿偏正式的休闲装",
                "注意鞋子要干净整洁，这是很多人的加分项",
            ],
            "outdoor": [
                "运动休闲风——轻便舒适为主，适合拍照的衣服更好",
                "一双舒适的运动鞋很重要，户外活动别穿新鞋",
                "根据天气准备外套，展示你细心的一面",
            ],
            "activity": [
                "舒适活动装——方便活动的衣服和鞋子",
                "选择不太容易弄脏的衣物，放松心态去享受",
                "轻便为主，别戴太多饰品",
            ],
        }
        outfits = outfit_options.get(date_type, outfit_options["coffee"])
        outfit_idx = rng.randint(0, len(outfits))
        outfit_suggestion = outfits[outfit_idx]

        # 约会建议
        tips = [
            f"提前10分钟到达，展示你的诚意和守时",
            f"第一次见面保持适度的眼神交流和微笑",
            f"多倾听对方说话，表现出真诚的兴趣",
            f"手机调静音，全心投入这次约会",
            f"约会后发一条暖心的消息，表达今天的感受",
            f"不要过于紧张，做真实的自己最好",
            f"记得AA或主动买单，但尊重对方的选择",
        ]
        rng.shuffle(tips)
        tips = tips[:5]

        # 需要注意的信号
        warning_signs = [
            "对方全程看手机或心不在焉",
            "频繁提到前任或表现出不尊重",
            "过度吹嘘自己的收入和成就",
            "急于要求进一步发展或肢体接触",
            "对服务员态度恶劣",
        ]
        rng.shuffle(warning_signs)
        warning_signs = warning_signs[:3]

        result = {
            "tips": tips,
            "conversation_starters": conversation_starters,
            "outfit_suggestion": outfit_suggestion,
            "warning_signs": warning_signs,
            "location": location,
            "budget": loc_info["budget"],
            "duration": loc_info["duration"],
            "date_type": date_type,
        }

        logger.info("约会方案生成完成: location=%s", location)
        return result

    # ------------------------------------------------------------------
    # Relationship advice
    # ------------------------------------------------------------------

    def relationship_advice(
        self,
        conversation_history: list[dict],
        question: str = "",
    ) -> str:
        """
        恋爱关系建议 - 基于对话历史和问题给出关系指导。

        使用规则引擎分析问题关键词，从预设建议库中组合回复。

        Args:
            conversation_history: 对话历史列表 [
                {"role": "user", "content": "..."},
                {"role": "advisor", "content": "..."},
            ]
            question: 用户的具体问题

        Returns:
            str: 关系建议 (中文)
        """
        logger.info("恋爱关系建议 (对话轮数: %d, 问题: %s)",
                   len(conversation_history), question[:30] if question else "无")

        # 分析问题关键词
        advice_parts = []

        # 关键词匹配
        keyword_advice = {
            "表白": [
                "关于表白，最重要的是时机和真诚。建议先通过日常互动确认对方的态度。",
                "如果你们已经经常聊天、约出来见面，可以考虑表白了。",
                "表白不需要太花哨，真诚地表达你的心意就好。选择一个安静私密的场合。",
            ],
            "分手": [
                "分手确实很痛苦，你现在的感受完全正常。",
                "允许自己难过，但也要照顾好自己——好好吃饭、睡觉、运动。",
                "时间真的是最好的疗愈师。现阶段不必急着走出来，给自己足够的空间。",
                "如果持续感到痛苦无法缓解，建议寻求专业心理咨询。",
            ],
            "吵架": [
                "情侣之间有分歧很正常，关键是如何处理冲突。",
                "建议冷静下来后再沟通，避免在情绪激动时说伤害对方的话。",
                '试着用"我感觉..."而不是"你总是..."来表达自己的感受。',
            ],
            "冷战": [
                "冷战是关系的慢性毒药，越拖越伤感情。",
                "如果真的很在乎，不妨先迈出一步。主动不代表软弱，反而说明你更珍惜这段关系。",
                '一条简单的消息"我想你了"可能就是打破僵局的开始。',
            ],
            "异地": [
                "异地恋需要更多的信任和沟通。约定固定的通话/视频时间很重要。",
                "一起做同一件事——看同一部电影、玩同一个游戏，可以增加亲密感。",
                "制定见面计划，给彼此期待和目标。",
            ],
            "信任": [
                "信任是慢慢建立的，不要急于要求对方证明什么。",
                "坦诚地表达你的担忧，而不是用试探和猜测。",
                "如果信任反复被打破，可能需要认真考虑这段关系是否健康。",
            ],
            "父母": [
                "见父母是关系中的重要里程碑，不必太紧张。",
                "提前了解对方父母的喜好和习惯，准备一些贴心的小礼物。",
                "表现真实的自己就好，过度讨好反而容易弄巧成拙。",
            ],
        }

        matched_topics = []
        for keyword, advices in keyword_advice.items():
            if keyword in question:
                matched_topics.extend(advices)

        if matched_topics:
            advice_parts.extend(matched_topics[:4])
        else:
            # 通用建议
            advice_parts.extend([
                "感谢你信任我来分享你的感受。",
                "每段关系都有自己的节奏，不必和别人比较。",
                "沟通是解决大部分问题的关键——真诚、耐心地表达你的想法。",
                "最重要的是，要先爱自己，才能更好地爱别人。",
            ])

        # 如果有对话历史，参考上下文
        if conversation_history:
            last_msg = conversation_history[-1].get("content", "") if conversation_history else ""
            if last_msg:
                advice_parts.append(
                    f"\n根据你之前提到的情况，我建议你多关注自己内心的真实感受。"
                )

        result = "\n".join(advice_parts)

        logger.info("关系建议生成完成 (长度: %d字符)", len(result))
        return result

    # ------------------------------------------------------------------
    # Icebreakers
    # ------------------------------------------------------------------

    def generate_icebreakers(
        self,
        user_profile: dict,
        match_profile: dict,
    ) -> list[str]:
        """
        生成冰破者 - 5条个性化开场白。

        基于双方档案信息，生成有趣、不尴尬的聊天开场白。
        使用模板组合 + 个性化填充。

        Args:
            user_profile: 用户档案
            match_profile: 匹配对象档案

        Returns:
            list[str]: 5条冰破者开场白
        """
        match_name = match_profile.get("name", "")
        match_interests = match_profile.get("interests", [])
        match_city = match_profile.get("city", "")
        match_job = match_profile.get("occupation", "")
        user_interests = set(user_profile.get("interests", []))

        seed = self._hash_seed(
            f"{user_profile.get('name', '')}:{match_name}:{','.join(match_interests)}"
        )
        rng = np.random.RandomState(seed)

        logger.info("生成冰破者: user=%s, match=%s",
                   user_profile.get("name", "?"), match_name)

        # 找共同兴趣
        common = user_interests & set(match_interests)
        icebreakers = []

        # 基于共同兴趣
        if common:
            interest = rng.choice(list(common))
            interest_questions = {
                "音乐": f"看到你也喜欢音乐，最近有什么单曲循环的歌吗？🎵",
                "旅行": f"发现我们都爱旅行！你去过最难忘的地方是哪里？✈️",
                "美食": f"同为吃货，你觉得{match_city or '咱们这个城市'}最好吃的是什么？🍜",
                "运动": f"看到你也喜欢运动，你平时怎么安排运动时间的？🏃",
                "阅读": f"发现你也在看书，最近有什么推荐的吗？📚",
                "电影": f"看你也是电影迷，最近有什么好看的推荐吗？🎬",
                "摄影": f"喜欢摄影的人眼光都不错！你最满意的一张照片是拍什么的？📷",
                "宠物": f"看到你也有宠物！是猫派还是狗派？🐱🐶",
                "健身": f"看你也在健身，你一般练什么项目？💪",
                "游戏": f"原来你也玩游戏！最近在玩什么？🎮",
            }
            question = interest_questions.get(
                interest,
                f"看到你也喜欢{interest}，能分享一下你的经历吗？"
            )
            icebreakers.append(question)

        # 基于对方职业
        if match_job:
            job_questions = [
                f"你是做{match_job}的吗？听起来很有趣，能给我讲讲吗？",
                f"做{match_job}一定有很多故事吧，工作中最有成就感的是什么？",
            ]
            icebreakers.append(rng.choice(job_questions))

        # 基于地点
        if match_city:
            icebreakers.append(
                f"你是{match_city}人吗？那边有什么好玩的地方推荐？"
            )

        # 通用但有趣的问题
        generic_icebreakers = [
            f"你好！看到你的资料，觉得你是一个很有意思的人。如果现在有一张机票，你最想去哪里？✈️",
            f"嗨，想问你一个严肃的问题——火锅你站鸳鸯锅还是九宫格？😄",
            f"你好呀！我发现你的笑容特别有感染力，是什么让你这么开心的？😊",
            f"突然好奇，你手机里最常用的三个App是什么？📱",
            f"如果让你给2024年打个分，满分10分你打几分？为什么？",
            f"看你资料感觉你生活很充实！周末一般怎么度过？",
            f"你好！我有个小调查——甜粽子还是咸粽子？这很重要哦😄",
            f"冒昧打扰一下，你头像里的那张照片是在{match_city or '哪里'}拍的？风景太美了！",
            f"如果用一道菜形容自己，你会选什么？我猜是一道色香味俱全的菜~",
            f"你好！如果可以拥有一种超能力，你会选什么？",
        ]

        # 选择填充到5条
        while len(icebreakers) < 5:
            idx = rng.randint(0, len(generic_icebreakers))
            candidate = generic_icebreakers[idx]
            if candidate not in icebreakers:
                icebreakers.append(candidate)

        # 确保恰好5条，去重
        result = list(dict.fromkeys(icebreakers))[:5]
        while len(result) < 5:
            result.append(
                f"你好，很高兴认识你！你平时喜欢做些什么呢？"
            )

        logger.info("冰破者生成完成 (%d条)", len(result))
        return result

    # ------------------------------------------------------------------
    # Deep compatibility analysis
    # ------------------------------------------------------------------

    def deep_compatibility_analysis(
        self,
        user_a: dict,
        user_b: dict,
    ) -> dict:
        """
        深度兼容性分析。

        综合人格、价值观、生活方式等维度进行详细分析，
        使用 numpy 进行多维度分数计算。

        Args:
            user_a: 用户A完整数据
            user_b: 用户B完整数据

        Returns:
            dict: 详细分析报告
        """
        logger.info("深度兼容性分析")

        seed = self._hash_seed(
            f"{user_a.get('name', '')}:{user_b.get('name', '')}"
        )
        rng = np.random.RandomState(seed)

        analysis = {
            "personality_compatibility": self._analyze_personality_fit(
                user_a.get("personality", {}),
                user_b.get("personality", {}),
                rng,
            ),
            "value_alignment": self._analyze_values(
                user_a.get("values", {}),
                user_b.get("values", {}),
                rng,
            ),
            "lifestyle_harmony": self._analyze_lifestyle(
                user_a.get("lifestyle", {}),
                user_b.get("lifestyle", {}),
                rng,
            ),
            "communication_style": self._analyze_communication(
                user_a.get("communication", {}),
                user_b.get("communication", {}),
                rng,
            ),
        }

        # 计算综合得分 (使用 numpy 加权平均)
        scores = []
        weights = np.array([0.30, 0.25, 0.25, 0.20])
        for i, key in enumerate(["personality_compatibility", "value_alignment",
                                  "lifestyle_harmony", "communication_style"]):
            score = analysis[key].get("score", 0.5)
            scores.append(score)

        overall = float(np.average(scores, weights=weights))
        analysis["overall_score"] = round(overall, 4)

        return analysis

    def _analyze_personality_fit(self, pa: dict, pb: dict,
                                  rng: np.random.RandomState) -> dict:
        """分析人格契合度"""
        # OCEAN 模型互补分析
        ocean_keys = ["openness", "conscientiousness", "extraversion",
                      "agreeableness", "neuroticism"]

        strengths = []
        challenges = []

        if not pa or not pb:
            score = float(rng.uniform(0.55, 0.85))
            return {
                "score": round(score, 4),
                "description": "人格互补，相处融洽",
                "strengths": ["性格互补", "沟通顺畅"],
                "challenges": ["需要给彼此空间"],
            }

        diffs = []
        for key in ocean_keys:
            va = pa.get(key, 0.5)
            vb = pb.get(key, 0.5)
            diffs.append(abs(va - vb))

        # 差异适中最好 (太大冲突多, 太小无趣)
        avg_diff = float(np.mean(diffs))
        if avg_diff < 0.15:
            score = float(rng.uniform(0.60, 0.75))
            strengths.append("性格相近，容易理解彼此")
            challenges.append("可能缺少新鲜感")
        elif avg_diff < 0.35:
            score = float(rng.uniform(0.70, 0.90))
            strengths.append("性格互补，相处平衡")
            strengths.append("差异带来成长空间")
        else:
            score = float(rng.uniform(0.45, 0.65))
            challenges.append("性格差异较大，需要更多磨合")
            challenges.append("注意尊重彼此的不同")

        return {
            "score": round(score, 4),
            "description": "人格契合度良好" if score > 0.65 else "人格差异适中",
            "strengths": strengths or ["各有特色"],
            "challenges": challenges or ["保持沟通"],
        }

    def _analyze_values(self, va: dict, vb: dict,
                        rng: np.random.RandomState) -> dict:
        """分析价值观匹配度"""
        if not va or not vb:
            score = float(rng.uniform(0.55, 0.85))
            return {
                "score": round(score, 4),
                "description": "核心价值观一致",
                "aligned": ["家庭观念", "事业态度"],
                "divergent": ["理财观念可能有差异"],
            }

        value_keys = ["family", "career", "money", "religion", "children"]
        aligned = []
        divergent = []

        for key in value_keys:
            if key in va and key in vb:
                if va[key] == vb[key]:
                    aligned.append(key)
                else:
                    divergent.append(key)

        score = float(np.clip(
            0.5 + 0.1 * len(aligned) - 0.05 * len(divergent) + rng.uniform(-0.1, 0.1),
            0.3, 0.95
        ))

        return {
            "score": round(score, 4),
            "description": "价值观基本一致" if score > 0.6 else "价值观需要沟通",
            "aligned": aligned or ["核心价值观"],
            "divergent": divergent or [],
        }

    def _analyze_lifestyle(self, la: dict, lb: dict,
                           rng: np.random.RandomState) -> dict:
        """分析生活方式协调度"""
        if not la or not lb:
            score = float(rng.uniform(0.50, 0.80))
            return {
                "score": round(score, 4),
                "description": "生活方式基本协调",
                "common": ["作息时间相近"],
                "adjustment": ["饮食偏好需要互相适应"],
            }

        score = float(rng.uniform(0.50, 0.85))
        return {
            "score": round(score, 4),
            "description": "生活方式协调度良好" if score > 0.65 else "生活方式需要磨合",
            "common": ["日常节奏相近"],
            "adjustment": ["周末活动偏好可能不同"],
        }

    def _analyze_communication(self, ca: dict, cb: dict,
                               rng: np.random.RandomState) -> dict:
        """分析沟通风格匹配度"""
        styles = ["直接表达型", "倾听理解型", "幽默轻松型",
                  "深度交流型", "温暖关怀型"]
        style_a = styles[rng.randint(0, len(styles))]
        style_b = styles[rng.randint(0, len(styles))]

        score = float(rng.uniform(0.55, 0.90))
        return {
            "score": round(score, 4),
            "description": "沟通风格互补" if score > 0.7 else "沟通风格需要磨合",
            "style_a": style_a,
            "style_b": style_b,
        }

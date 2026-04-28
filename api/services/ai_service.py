"""
Minder AI 红娘 - AI 引擎服务

提供语音分析、人脸分析、约会建议、AI对话等功能的接口层。
实际生产中对接各 AI 模型服务, 当前为模拟实现。
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from minder.db.models import User


# ==================== 数据结构 ====================

@dataclass
class VoiceAnalysis:
    """语音分析结果"""
    pitch_mean: float = 0.0          # 平均音高
    pitch_std: float = 0.0           # 音高标准差
    speech_rate: float = 0.0         # 语速 (字/秒)
    energy_mean: float = 0.0         # 平均能量
    tone_quality: str = "neutral"    # 音色质量: warm/neutral/cold
    emotion: str = "calm"            # 情感状态: calm/excited/nervous/sad
    confidence: float = 0.0          # 分析置信度
    voice_embedding: List[float] = field(default_factory=list)  # 声音向量
    summary: str = ""                # 文字总结


@dataclass
class FaceAnalysis:
    """面部分析结果"""
    attractiveness_score: float = 0.0  # 颜值评分 (0-100)
    symmetry_score: float = 0.0        # 对称性评分
    expression: str = "neutral"        # 表情: smile/neutral/sad/surprised
    age_estimate: int = 0             # 估计年龄
    gender_estimate: str = ""          # 估计性别
    skin_health: float = 0.0          # 皮肤健康度
    face_embedding: List[float] = field(default_factory=list)  # 面部向量
    summary: str = ""


@dataclass
class ChatContext:
    """AI对话上下文"""
    user_profile: Optional[Dict] = None
    match_profile: Optional[Dict] = None
    conversation_history: List[Dict] = field(default_factory=list)
    topic: Optional[str] = None


# ==================== 模拟数据 ====================

PERSONALITY_DESCRIPTIONS = {
    "外向": "热情开朗, 善于社交, 喜欢与人互动",
    "内向": "沉稳内敛, 善于思考, 喜欢安静的环境",
    "理性": "逻辑清晰, 做事有条理, 善于分析问题",
    "感性": "情感丰富, 富有同理心, 重视内心感受",
    "乐观": "积极向上, 看到事物好的一面, 感染力强",
    "沉稳": "成熟稳重, 不轻易冲动, 处事冷静",
}

DATE_VENUES = {
    "咖啡": ["精品咖啡馆", "书店咖啡角", "湖畔茶室", "文艺小馆"],
    "美食": ["创意料理餐厅", "本地特色小吃街", "甜品工作室", "烹饪课堂"],
    "户外": ["城市公园", "滨江步道", "植物园", "骑行绿道"],
    "文化": ["美术馆", "独立书店", "手作工坊", "话剧/音乐剧"],
    "运动": ["攀岩馆", "瑜伽工作室", "羽毛球馆", "滑冰场"],
}


# ==================== AI 服务函数 ====================

async def analyze_voice(audio_data: bytes) -> VoiceAnalysis:
    """
    分析语音数据。

    在生产环境中, 此函数会:
    1. 调用语音识别模型 (如 Whisper) 转录文字
    2. 提取声音特征 (音高、语速、能量)
    3. 使用声纹模型生成声音嵌入向量
    4. 分析情感状态

    当前为模拟实现。
    """
    # 模拟分析延迟 (实际会调用远程模型)
    embedding = [random.uniform(-1.0, 1.0) for _ in range(128)]
    # 归一化
    norm = sum(x * x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]

    tones = ["warm", "neutral", "clear", "deep", "bright"]
    emotions = ["calm", "confident", "gentle", "enthusiastic", "cheerful"]

    tone = random.choice(tones)
    emotion = random.choice(emotions)

    summary_map = {
        ("warm", "calm"): "声音温暖沉稳, 给人安心感, 适合深入交流",
        ("warm", "enthusiastic"): "声音温暖热情, 充满活力, 让人感到亲近",
        ("deep", "confident"): "声音低沉有力, 自信从容, 有成熟魅力",
        ("bright", "cheerful"): "声音明亮清脆, 充满朝气, 让人愉悦",
        ("neutral", "gentle"): "声音平和温柔, 不急不缓, 舒适自然",
    }
    default_summary = f"声音{tone}, 情感{emotion}, 整体印象良好"
    summary = summary_map.get((tone, emotion), default_summary)

    return VoiceAnalysis(
        pitch_mean=random.uniform(100, 300),
        pitch_std=random.uniform(20, 60),
        speech_rate=random.uniform(2.5, 5.0),
        energy_mean=random.uniform(0.3, 0.8),
        tone_quality=tone,
        emotion=emotion,
        confidence=random.uniform(0.7, 0.95),
        voice_embedding=embedding,
        summary=summary,
    )


async def analyze_face(image_data: bytes) -> FaceAnalysis:
    """
    分析面部图像。

    在生产环境中, 此函数会:
    1. 人脸检测和对齐
    2. 提取面部特征向量
    3. 分析面部属性 (表情、年龄等)
    4. 使用审美模型评分

    注意: 我们强调健康美, 不做单一审美标准评分。
    当前为模拟实现。
    """
    embedding = [random.uniform(-1.0, 1.0) for _ in range(128)]
    norm = sum(x * x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]

    expressions = ["smile", "neutral", "gentle_smile", "confident"]
    expression = random.choice(expressions)

    attractiveness = random.gauss(70, 12)
    attractiveness = max(30, min(95, attractiveness))

    return FaceAnalysis(
        attractiveness_score=round(attractiveness, 1),
        symmetry_score=round(random.uniform(0.7, 0.98), 2),
        expression=expression,
        age_estimate=random.randint(20, 45),
        gender_estimate=random.choice(["male", "female"]),
        skin_health=round(random.uniform(0.6, 0.95), 2),
        face_embedding=embedding,
        summary=f"面部对称性良好, 表情{expression}, 整体气质自然大方",
    )


async def generate_date_advice(
    user: User,
    match_user: User,
    scenario: Optional[str] = None
) -> dict:
    """
    生成约会建议。

    基于双方的性格标签、兴趣爱好, 生成个性化的约会方案。

    Args:
        user: 当前用户
        match_user: 匹配对象
        scenario: 指定场景 (可选)

    Returns:
        {
            "tips": [...],
            "venue_suggestions": [...],
            "conversation_starters": [...],
            "timing_advice": str,
            "dressing_advice": str,
        }
    """
    user_tags = set(user.personality_tags or []) | set(user.lifestyle_tags or [])
    match_tags = set(match_user.personality_tags or []) | set(match_user.lifestyle_tags or [])
    common = user_tags & match_tags

    # 根据共同兴趣推荐场景
    if not scenario:
        if common & {"美食", "烹饪", "吃货"}:
            scenario = "美食"
        elif common & {"户外", "运动", "健身", "跑步", "骑行"}:
            scenario = "运动"
        elif common & {"阅读", "艺术", "电影", "音乐", "文化"}:
            scenario = "文化"
        elif common & {"咖啡", "下午茶"}:
            scenario = "咖啡"
        else:
            scenario = random.choice(list(DATE_VENUES.keys()))

    venues = DATE_VENUES.get(scenario, DATE_VENUES["咖啡"])

    # 生成约会建议
    tips = [
        f"根据你们的共同兴趣, 建议选择{scenario}主题的约会",
        "第一次见面建议选择公共场所, 时间控制在1-2小时",
        "保持真诚和好奇心, 多倾听对方的想法",
        "可以聊聊各自的兴趣爱好和最近的生活趣事",
        "放松心态, 享受交流的过程, 不要给自己太大压力",
    ]

    if "内向" in (match_user.personality_tags or []):
        tips.append("对方性格偏内向, 建议选择安静舒适的环境, 避免过于嘈杂的场所")
    if "外向" in (match_user.personality_tags or []):
        tips.append("对方性格外向, 可以尝试一些互动性强的活动")

    # 开场白建议
    starters = []
    if common:
        tag = random.choice(list(common))
        starters.append(f"你也喜欢{tag}吗? 我最近...")
    starters.extend([
        "最近有看什么好看的电影/剧吗?",
        "平时周末一般怎么度过?",
        "你最想去旅行的地方是哪里?",
    ])

    return {
        "tips": tips[:6],
        "venue_suggestions": random.sample(venues, min(3, len(venues))),
        "conversation_starters": starters[:4],
        "timing_advice": "建议提前3-5天邀约, 选择周末下午或工作日晚上",
        "dressing_advice": "得体大方, 体现个人风格, 不必过于正式",
    }


async def chat_with_advisor(
    message: str,
    context: Optional[ChatContext] = None
) -> dict:
    """
    与 AI 红娘对话。

    AI红娘是一个智能助手, 可以:
    - 回答婚恋相关问题
    - 提供约会建议
    - 分析匹配情况
    - 给出情感指导

    在生产环境中, 此函数会调用大语言模型 (如 GPT/LLaMA)。
    当前为基于规则的模拟实现。

    Returns:
        {"reply": str, "suggestions": [str]}
    """
    message_lower = message.lower()

    # 情感关键词匹配
    if any(kw in message for kw in ["紧张", "焦虑", "不安", "害怕", "担心"]):
        return {
            "reply": (
                "你的紧张感完全正常! 每个人在开始新的感情时都会有这样的感受。"
                "试着把注意力放在对方身上, 而不是自己的表现上。"
                "真诚和自然是最吸引人的品质。记住, 约会不是面试, "
                "而是两个人互相了解、享受在一起时光的过程。"
                "深呼吸, 做真实的自己就好。😊"
            ),
            "suggestions": [
                "第一次约会选在哪里比较好?",
                "怎么准备约会话题?",
                "约会后多久联系对方合适?",
            ]
        }

    if any(kw in message for kw in ["不知道聊什么", "没话题", "尴尬", "冷场"]):
        return {
            "reply": (
                "聊天的关键是好奇心和倾听。可以从这些话题入手:\n"
                "1. 旅行经历 - '你去过最喜欢的地方是哪里?'\n"
                "2. 美食探索 - '你喜欢什么类型的菜系?'\n"
                "3. 兴趣爱好 - '平时下班后一般做什么?'\n"
                "4. 梦想目标 - '如果有一个月假期, 你会做什么?'\n\n"
                "记住: 好的对话是双向的, 多问开放性问题, "
                "然后根据对方的回答深入聊下去。"
            ),
            "suggestions": [
                "有哪些约会禁忌需要注意?",
                "怎么判断对方是否对我有好感?",
                "第一次约会要AA还是请客?",
            ]
        }

    if any(kw in message for kw in ["匹配", "推荐", "对象", "找"]):
        return {
            "reply": (
                "根据你的资料和偏好, 我正在为你精心筛选匹配对象。"
                "好的匹配需要综合考虑性格、价值观、生活方式等多个维度。"
                "建议你:\n"
                "1. 完善个人资料, 尤其是性格和价值观标签\n"
                "2. 上传语音和照片, 提高匹配精准度\n"
                "3. 每天查看推荐, 主动出击\n"
                "4. 保持开放心态, 不要局限于单一类型"
            ),
            "suggestions": [
                "如何完善我的个人资料?",
                "提高匹配成功率的技巧?",
                "看看今天的推荐",
            ]
        }

    if any(kw in message for kw in ["分手", "失恋", "难过", "伤心"]):
        return {
            "reply": (
                "我能感受到你现在的心情。失恋确实很痛苦, 但这也是一段成长的经历。\n"
                "给自己时间去消化这些情绪, 不要急于走出来。\n"
                "可以尝试:\n"
                "• 和信任的朋友倾诉\n"
                "• 做一些让自己开心的事\n"
                "• 重新审视自己的需求和期望\n"
                "当你准备好了, 我会在这里帮你找到更合适的人。💪"
            ),
            "suggestions": [
                "多久可以开始新的恋情?",
                "怎么从失恋中走出来?",
                "如何避免重蹈覆辙?",
            ]
        }

    # 默认回复
    return {
        "reply": (
            f"你好! 我是AI红娘小缘 🌹\n\n"
            "我可以帮你:\n"
            "• 分析你的匹配对象\n"
            "• 提供约会建议\n"
            "• 解答情感困惑\n"
            "• 优化个人资料\n\n"
            "有什么我可以帮你的吗?"
        ),
        "suggestions": [
            "帮我分析一下最近的匹配",
            "我想提高匹配成功率",
            "第一次约会有什么建议?",
        ]
    }


async def deep_analyze_match(
    db: AsyncSession,
    user_a: User,
    user_b: User
) -> dict:
    """
    深度匹配分析。

    提供两个用户之间的详细匹配报告。

    Returns:
        {
            "overall_score": float,
            "dimension_scores": dict,
            "strengths": [str],
            "concerns": [str],
            "advice": str,
        }
    """
    from minder.api.services.matching_service import calculate_compatibility

    total, dim_scores = calculate_compatibility(user_a, user_b)

    strengths = []
    concerns = []

    # 分析各维度
    if dim_scores["personality"] >= 0.7:
        strengths.append("性格互补性高, 相处会比较融洽")
    if dim_scores["values"] >= 0.7:
        strengths.append("价值观相近, 长期关系稳定性高")
    if dim_scores["lifestyle"] >= 0.6:
        strengths.append("生活方式相似, 容易找到共同话题")
    if dim_scores["voice"] >= 0.6:
        strengths.append("声音气质契合, 沟通体验良好")

    if dim_scores["values"] < 0.4:
        concerns.append("价值观差异较大, 可能在重要决定上产生分歧")
    if dim_scores["lifestyle"] < 0.3:
        concerns.append("生活习惯差异较大, 需要互相包容和适应")
    if dim_scores["personality"] < 0.4:
        concerns.append("性格匹配度偏低, 初期可能需要更多磨合")

    if not strengths:
        strengths.append("虽然匹配分数不是最高, 但感情中真诚和努力更重要")
    if not concerns:
        concerns.append("目前没有明显的匹配障碍")

    # 生成建议
    advice_parts = [f"综合匹配度 {total*100:.1f}%"]
    if total >= 0.75:
        advice_parts.append("这是一对非常有潜力的组合! 建议主动发起对话, 约一次见面。")
    elif total >= 0.55:
        advice_parts.append("匹配度不错, 建议多了解对方, 可以先从线上聊天开始。")
    else:
        advice_parts.append("匹配度中等, 但如果双方都有诚意, 也值得尝试。")

    return {
        "overall_score": total,
        "dimension_scores": dim_scores,
        "strengths": strengths,
        "concerns": concerns,
        "advice": " ".join(advice_parts),
    }

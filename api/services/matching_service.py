"""
Minder AI 红娘 - 核心匹配算法服务

实现基于多维加权的智能匹配引擎。
权重分配:
  - 声音匹配 (Voice):      20%
  - 颜值匹配 (Face):        15%
  - 性格匹配 (Personality):  25%
  - 价值观匹配 (Values):     20%
  - 健康匹配 (Health):       10%
  - 生活方式 (Lifestyle):    10%
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select, and_, or_, func, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from minder.db.models import User, Match, MatchStatus, Gender, SubscriptionTier


# ==================== 权重配置 ====================

WEIGHTS = {
    "voice": 0.20,
    "face": 0.15,
    "personality": 0.25,
    "values": 0.20,
    "health": 0.10,
    "lifestyle": 0.10,
}

# VIP 用户每日匹配上限
MATCH_LIMITS = {
    SubscriptionTier.FREE: 5,
    SubscriptionTier.BASIC: 15,
    SubscriptionTier.VIP: 30,
    SubscriptionTier.SVIP: 999,
}


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _tag_overlap_score(tags_a: List[str], tags_b: List[str]) -> float:
    """计算标签重叠度得分 (Jaccard 相似度)"""
    if not tags_a or not tags_b:
        return 0.0
    set_a, set_b = set(tags_a), set(tags_b)
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _age_from_birth(birth_date: datetime) -> int:
    """从出生日期计算年龄"""
    today = datetime.utcnow()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def _age_compatibility(age_a: int, age_b: int) -> float:
    """年龄差兼容性 (差越小分数越高, 最大容忍15岁)"""
    diff = abs(age_a - age_b)
    if diff <= 3:
        return 1.0
    elif diff <= 5:
        return 0.9
    elif diff <= 8:
        return 0.7
    elif diff <= 12:
        return 0.5
    elif diff <= 15:
        return 0.3
    else:
        return 0.1


def _city_match(city_a: Optional[str], city_b: Optional[str]) -> float:
    """城市匹配得分"""
    if not city_a or not city_b:
        return 0.5  # 未知时给中间分
    return 1.0 if city_a.strip() == city_b.strip() else 0.3


def _education_level(edu: Optional[str]) -> int:
    """学历等级映射"""
    if not edu:
        return 0
    levels = {
        "高中": 1, "大专": 2, "本科": 3, "学士": 3,
        "硕士": 4, "研究生": 4, "博士": 5, "博士后": 6,
    }
    for key, val in levels.items():
        if key in edu:
            return val
    return 2


# ==================== 核心匹配函数 ====================

def calculate_voice_score(user_a: User, user_b: User) -> float:
    """
    计算声音匹配度 (20%)

    基于用户的声音嵌入向量进行余弦相似度计算。
    如果任一方未上传声音样本，则返回基于性格的估算分数。
    """
    vec_a = user_a.voice_embedding
    vec_b = user_b.voice_embedding

    if vec_a and vec_b and len(vec_a) > 0 and len(vec_b) > 0:
        return _cosine_similarity(vec_a, vec_b)

    # 无声音数据时, 用性格标签做保守估算
    personality_bonus = _tag_overlap_score(
        user_a.personality_tags or [], user_b.personality_tags or []
    )
    return 0.4 + personality_bonus * 0.3  # 0.4 ~ 0.7


def calculate_face_score(user_a: User, user_b: User) -> float:
    """
    计算颜值匹配度 (15%)

    基于面部嵌入向量计算相似度。
    注意: 这不是"好看程度", 而是面部特征的匹配偏好。
    """
    vec_a = user_a.face_embedding
    vec_b = user_b.face_embedding

    if vec_a and vec_b and len(vec_a) > 0 and len(vec_b) > 0:
        # 面部匹配使用调整后的余弦相似度
        raw = _cosine_similarity(vec_a, vec_b)
        # 将分数映射到更合理的范围 (0.3 ~ 0.95)
        return 0.3 + raw * 0.65

    # 无面部数据时返回中等分数
    return 0.5


def calculate_personality_score(user_a: User, user_b: User) -> float:
    """
    计算性格匹配度 (25%)

    多维度性格分析:
    1. 性格向量余弦相似度 (如果有的话)
    2. 性格标签匹配度
    3. 互补性格加成 (外向配内向等)
    """
    score = 0.0

    # 1. 向量相似度 (40%)
    vec_a = user_a.personality_vector
    vec_b = user_b.personality_vector
    if vec_a and vec_b and len(vec_a) > 0 and len(vec_b) > 0:
        vec_score = _cosine_similarity(vec_a, vec_b)
        score += vec_score * 0.4
    else:
        score += 0.2  # 默认分

    # 2. 标签匹配 (40%)
    tags_a = user_a.personality_tags or []
    tags_b = user_b.personality_tags or []
    tag_score = _tag_overlap_score(tags_a, tags_b)
    score += tag_score * 0.4

    # 3. 互补性格加成 (20%)
    complement_pairs = [
        ("外向", "内向"), ("理性", "感性"), ("计划型", "随性"),
        ("话多", "安静"), ("主动", "被动"),
    ]
    complement_bonus = 0.0
    for a_tag, b_tag in complement_pairs:
        if (a_tag in tags_a and b_tag in tags_b) or (b_tag in tags_a and a_tag in tags_b):
            complement_bonus += 0.04  # 每对互补加0.04
    complement_bonus = min(0.2, complement_bonus)
    score += complement_bonus

    return min(1.0, max(0.0, score))


def calculate_values_score(user_a: User, user_b: User) -> float:
    """
    计算价值观匹配度 (20%)

    价值观匹配对长期关系至关重要。
    主要分析: 家庭观、事业观、金钱观、人生目标。
    """
    score = 0.0

    # 1. 向量相似度 (50%)
    vec_a = user_a.values_vector
    vec_b = user_b.values_vector
    if vec_a and vec_b and len(vec_a) > 0 and len(vec_b) > 0:
        score += _cosine_similarity(vec_a, vec_b) * 0.5
    else:
        score += 0.25

    # 2. 价值观标签匹配 (50%)
    tags_a = user_a.values_tags or []
    tags_b = user_b.values_tags or []

    # 核心价值观必须高度一致
    core_values = {"家庭优先", "事业心强", "经济独立", "精神追求", "传统保守", "开放自由"}
    core_a = set(tags_a) & core_values
    core_b = set(tags_b) & core_values

    if core_a and core_b:
        core_overlap = len(core_a & core_b) / max(len(core_a | core_b), 1)
        score += core_overlap * 0.3
    else:
        score += 0.15

    # 其他价值观标签
    other_score = _tag_overlap_score(tags_a, tags_b)
    score += other_score * 0.2

    return min(1.0, max(0.0, score))


def calculate_health_score(user_a: User, user_b: User) -> float:
    """
    计算健康匹配度 (10%)

    基于双方的健康评估分数和生活方式的健康维度。
    """
    score_a = (user_a.health_score or 50.0) / 100.0
    score_b = (user_b.health_score or 50.0) / 100.0

    # 健康水平接近度 (差异小更好)
    avg = (score_a + score_b) / 2
    diff = abs(score_a - score_b)
    closeness = 1.0 - diff

    # 综合: 平均健康水平 + 接近度
    return avg * 0.6 + closeness * 0.4


def calculate_lifestyle_score(user_a: User, user_b: User) -> float:
    """
    计算生活方式匹配度 (10%)

    兴趣爱好、作息习惯、消费观念等。
    """
    tags_a = user_a.lifestyle_tags or []
    tags_b = user_b.lifestyle_tags or []

    if not tags_a and not tags_b:
        return 0.5

    # 重叠度
    overlap = _tag_overlap_score(tags_a, tags_b)

    # 兴趣互补加成 (有共同爱好 + 各自独特爱好)
    set_a, set_b = set(tags_a), set(tags_b)
    common = set_a & set_b
    unique_a = set_a - set_b
    unique_b = set_b - set_a

    # 有些共同爱好很重要, 但不需要完全一致
    common_bonus = min(0.3, len(common) * 0.1)
    diversity_bonus = 0.0
    if unique_a and unique_b:
        diversity_bonus = 0.1  # 双方有不同兴趣, 可以互相带入新世界

    score = overlap * 0.6 + common_bonus + diversity_bonus
    return min(1.0, max(0.0, score))


def calculate_compatibility(user_a: User, user_b: User) -> Tuple[float, dict]:
    """
    计算两个用户的综合兼容性分数。

    返回:
        (total_score, {
            "voice": float,
            "face": float,
            "personality": float,
            "values": float,
            "health": float,
            "lifestyle": float
        })

    总分范围: 0.0 ~ 1.0
    """
    scores = {
        "voice": calculate_voice_score(user_a, user_b),
        "face": calculate_face_score(user_a, user_b),
        "personality": calculate_personality_score(user_a, user_b),
        "values": calculate_values_score(user_a, user_b),
        "health": calculate_health_score(user_a, user_b),
        "lifestyle": calculate_lifestyle_score(user_a, user_b),
    }

    # 加权求和
    total = sum(scores[dim] * WEIGHTS[dim] for dim in WEIGHTS)

    # 年龄兼容性修正 (±5%)
    age_a = _age_from_birth(user_a.birth_date)
    age_b = _age_from_birth(user_b.birth_date)
    age_factor = _age_compatibility(age_a, age_b)
    total = total * (0.95 + age_factor * 0.05)

    # 同城加分 (±3%)
    city_factor = _city_match(user_a.city, user_b.city)
    total = total * (0.97 + city_factor * 0.03)

    total = min(1.0, max(0.0, total))

    # 四舍五入到小数点后4位
    scores = {k: round(v, 4) for k, v in scores.items()}
    total = round(total, 4)

    return total, scores


async def get_daily_matches(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    page: int = 1
) -> Tuple[List[dict], int]:
    """
    获取每日推荐匹配列表。

    算法流程:
    1. 获取用户资料
    2. 筛选符合条件的候选用户
    3. 对每个候选用户计算兼容性
    4. 按分数排序, 返回 top-N

    Args:
        db: 数据库会话
        user_id: 当前用户ID
        limit: 每页数量
        page: 页码

    Returns:
        (candidates_list, total_count)
    """
    # 1. 获取当前用户
    result = await db.execute(select(User).where(User.id == user_id))
    current_user = result.scalar_one_or_none()
    if not current_user:
        return [], 0

    # 2. 获取用户匹配限制
    match_limit = MATCH_LIMITS.get(current_user.subscription_tier, 5)

    # 3. 已经匹配过的用户ID (排除)
    stmt = select(Match).where(
        or_(Match.user_a_id == user_id, Match.user_b_id == user_id)
    )
    result = await db.execute(stmt)
    existing_matches = result.scalars().all()
    seen_user_ids = set()
    for m in existing_matches:
        seen_user_ids.add(m.user_a_id)
        seen_user_ids.add(m.user_b_id)
    seen_user_ids.discard(user_id)

    # 4. 筛选候选用户
    now = datetime.utcnow()
    age_min = current_user.preferred_age_min or 18
    age_max = current_user.preferred_age_max or 60
    birth_max = datetime(now.year - age_min, now.month, now.day)
    birth_min = datetime(now.year - age_max - 1, now.month, now.day)

    conditions = [
        User.id != user_id,
        User.is_active == True,
        User.id.notin_(seen_user_ids) if seen_user_ids else True,
        User.birth_date >= birth_min,
        User.birth_date <= birth_max,
    ]

    # 偏好性别筛选
    if current_user.preferred_gender:
        conditions.append(User.gender == current_user.preferred_gender)

    # 偏好城市筛选 (非强制)
    # 如果设置了偏好城市, 优先推荐同城, 但也包含其他城市
    stmt = select(User).where(and_(*conditions)).options(
        selectinload(User.photos)
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    if not candidates:
        return [], 0

    # 5. 计算兼容性分数
    scored_candidates = []
    for candidate in candidates:
        total_score, dim_scores = calculate_compatibility(current_user, candidate)

        # 同城优先加分
        if current_user.preferred_city and candidate.city:
            if current_user.preferred_city == candidate.city:
                total_score = min(1.0, total_score + 0.03)

        scored_candidates.append({
            "user": candidate,
            "total_score": total_score,
            "dim_scores": dim_scores,
        })

    # 6. 排序 (分数从高到低)
    scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)

    # 7. 分页
    total = min(len(scored_candidates), match_limit)
    start = (page - 1) * limit
    end = start + limit
    page_candidates = scored_candidates[start:end]

    return page_candidates, total


async def rank_candidates(
    db: AsyncSession,
    user_id: int,
    candidate_ids: List[int]
) -> List[dict]:
    """
    对指定候选用户进行排名。

    用于更精确的匹配推荐, 如"精选推荐"功能。

    Args:
        db: 数据库会话
        user_id: 当前用户ID
        candidate_ids: 候选用户ID列表

    Returns:
        按兼容性排序的候选列表
    """
    result = await db.execute(select(User).where(User.id == user_id))
    current_user = result.scalar_one_or_none()
    if not current_user:
        return []

    result = await db.execute(
        select(User).where(User.id.in_(candidate_ids)).options(selectinload(User.photos))
    )
    candidates = result.scalars().all()

    scored = []
    for candidate in candidates:
        total_score, dim_scores = calculate_compatibility(current_user, candidate)
        scored.append({
            "user": candidate,
            "total_score": total_score,
            "dim_scores": dim_scores,
        })

    scored.sort(key=lambda x: x["total_score"], reverse=True)
    return scored


async def create_match_record(
    db: AsyncSession,
    user_a_id: int,
    user_b_id: int
) -> Optional[Match]:
    """
    创建匹配记录。

    确保 user_a_id < user_b_id 以避免重复。
    """
    # 规范化顺序
    if user_a_id > user_b_id:
        user_a_id, user_b_id = user_b_id, user_a_id

    # 检查是否已存在
    stmt = select(Match).where(
        Match.user_a_id == user_a_id,
        Match.user_b_id == user_b_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # 获取用户并计算分数
    result_a = await db.execute(select(User).where(User.id == user_a_id))
    user_a = result_a.scalar_one_or_none()
    result_b = await db.execute(select(User).where(User.id == user_b_id))
    user_b = result_b.scalar_one_or_none()

    if not user_a or not user_b:
        return None

    total_score, dim_scores = calculate_compatibility(user_a, user_b)

    match = Match(
        user_a_id=user_a_id,
        user_b_id=user_b_id,
        compatibility_score=total_score,
        voice_score=dim_scores["voice"],
        face_score=dim_scores["face"],
        personality_score=dim_scores["personality"],
        values_score=dim_scores["values"],
        health_score=dim_scores["health"],
        lifestyle_score=dim_scores["lifestyle"],
        status_a=MatchStatus.PENDING,
        status_b=MatchStatus.PENDING,
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


async def handle_accept(
    db: AsyncSession,
    match_id: int,
    user_id: int
) -> Tuple[bool, bool]:
    """
    处理用户接受匹配。

    返回: (success, is_mutual)
    """
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        return False, False

    if match.user_a_id == user_id:
        match.status_a = MatchStatus.ACCEPTED
    elif match.user_b_id == user_id:
        match.status_b = MatchStatus.ACCEPTED
    else:
        return False, False

    # 检查是否双向接受
    is_mutual = (
        match.status_a == MatchStatus.ACCEPTED and
        match.status_b == MatchStatus.ACCEPTED
    )
    match.is_mutual = is_mutual
    match.updated_at = datetime.utcnow()

    await db.commit()
    return True, is_mutual


async def handle_reject(
    db: AsyncSession,
    match_id: int,
    user_id: int
) -> bool:
    """处理用户拒绝匹配"""
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        return False

    if match.user_a_id == user_id:
        match.status_a = MatchStatus.REJECTED
    elif match.user_b_id == user_id:
        match.status_b = MatchStatus.REJECTED
    else:
        return False

    match.updated_at = datetime.utcnow()
    await db.commit()
    return True

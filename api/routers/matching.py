"""
Minder AI 红娘 - 匹配路由

处理发现推荐、接受/拒绝匹配、查看匹配列表等功能。
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from minder.db import get_db, User, Match, MatchStatus, Gender
from minder.schemas import (
    DiscoverResponse, MatchCandidate, MatchDetail,
    UserPublicProfile, SuccessResponse, ErrorResponse
)
from minder.api.routers.auth import get_current_user
from minder.api.services.matching_service import (
    get_daily_matches, handle_accept, handle_reject,
    create_match_record
)

router = APIRouter(prefix="/matching", tags=["匹配"])


def _user_to_public(user: User) -> UserPublicProfile:
    """转换用户为公开资料"""
    from minder.api.routers.users import _user_to_public as convert
    return convert(user)


@router.get("/discover", response_model=DiscoverResponse, summary="发现推荐")
async def discover(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取每日推荐匹配列表。

    基于AI匹配算法, 为用户推荐最合适的匹配对象。
    免费用户每日5个推荐, VIP用户30个。
    """
    candidates, total = await get_daily_matches(
        db, current_user.id, limit=page_size, page=page
    )

    match_candidates = []
    for cand in candidates:
        user = cand["user"]
        # 计算年龄
        age = _age_from_birth(user.birth_date)

        match_candidates.append(MatchCandidate(
            user=UserPublicProfile(
                id=user.id,
                nickname=user.nickname,
                gender=user.gender.value if isinstance(user.gender, Gender) else user.gender,
                age=age,
                city=user.city,
                bio=user.bio,
                occupation=user.occupation,
                education=user.education,
                height_cm=user.height_cm,
                avatar_url=user.avatar_url,
                personality_tags=user.personality_tags or [],
                values_tags=user.values_tags or [],
                lifestyle_tags=user.lifestyle_tags or [],
                photos=[p.url for p in (user.photos or [])],
            ),
            compatibility_score=cand["total_score"],
            voice_score=cand["dim_scores"]["voice"],
            face_score=cand["dim_scores"]["face"],
            personality_score=cand["dim_scores"]["personality"],
            values_score=cand["dim_scores"]["values"],
            health_score=cand["dim_scores"]["health"],
            lifestyle_score=cand["dim_scores"]["lifestyle"],
            match_id=0,  # 匹配ID在创建时生成
        ))

    return DiscoverResponse(
        candidates=match_candidates,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


def _age_from_birth(birth_date):
    today = datetime.utcnow()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


@router.post("/match/{user_id}/accept", response_model=SuccessResponse, summary="接受匹配")
async def accept_match(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    接受一个匹配对象。

    如果双方都接受了, 则形成互相匹配, 可以开始聊天。
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能与自己匹配")

    # 查找或创建匹配记录
    a_id = min(current_user.id, user_id)
    b_id = max(current_user.id, user_id)

    result = await db.execute(
        select(Match).where(Match.user_a_id == a_id, Match.user_b_id == b_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        # 创建新的匹配记录
        match = await create_match_record(db, a_id, b_id)
        if not match:
            raise HTTPException(status_code=400, detail="创建匹配失败")

    success, is_mutual = await handle_accept(db, match.id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="操作失败")

    message = "匹配成功! 你们可以开始聊天了" if is_mutual else "已接受, 等待对方回应"
    return SuccessResponse(message=message, data={"is_mutual": is_mutual, "match_id": match.id})


@router.post("/match/{user_id}/reject", response_model=SuccessResponse, summary="拒绝匹配")
async def reject_match(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    拒绝一个匹配对象。
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="无效操作")

    a_id = min(current_user.id, user_id)
    b_id = max(current_user.id, user_id)

    result = await db.execute(
        select(Match).where(Match.user_a_id == a_id, Match.user_b_id == b_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        match = await create_match_record(db, a_id, b_id)
        if not match:
            raise HTTPException(status_code=400, detail="创建匹配记录失败")

    success = await handle_reject(db, match.id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="操作失败")

    return SuccessResponse(message="已拒绝")


@router.get("/matches", response_model=List[MatchDetail], summary="我的匹配列表")
async def get_my_matches(
    mutual_only: bool = Query(False, description="仅显示互相匹配"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我的匹配列表。

    mutual_only=True: 仅显示双方都接受的匹配
    mutual_only=False: 显示所有匹配 (包括待确认的)
    """
    conditions = [
        or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id)
    ]
    if mutual_only:
        conditions.append(Match.is_mutual == True)

    result = await db.execute(
        select(Match)
        .where(and_(*conditions))
        .order_by(Match.updated_at.desc())
        .options(selectinload(Match.user_a), selectinload(Match.user_b))
    )
    matches = result.scalars().all()

    match_list = []
    for m in matches:
        partner = m.user_b if m.user_a_id == current_user.id else m.user_a

        # 获取当前用户的状态
        my_status = m.status_a if m.user_a_id == current_user.id else m.status_b
        status_val = my_status.value if hasattr(my_status, 'value') else my_status

        match_list.append(MatchDetail(
            id=m.id,
            partner=_user_to_public(partner),
            compatibility_score=m.compatibility_score,
            dimension_scores={
                "voice": m.voice_score,
                "face": m.face_score,
                "personality": m.personality_score,
                "values": m.values_score,
                "health": m.health_score,
                "lifestyle": m.lifestyle_score,
            },
            status=status_val,
            is_mutual=m.is_mutual,
            created_at=m.created_at,
        ))

    return match_list


@router.get("/matches/{match_id}", response_model=MatchDetail, summary="匹配详情")
async def get_match_detail(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定匹配的详细信息。
    """
    result = await db.execute(
        select(Match)
        .where(Match.id == match_id)
        .options(selectinload(Match.user_a), selectinload(Match.user_b))
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="匹配不存在")

    if match.user_a_id != current_user.id and match.user_b_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此匹配")

    partner = match.user_b if match.user_a_id == current_user.id else match.user_a
    my_status = match.status_a if match.user_a_id == current_user.id else match.status_b
    status_val = my_status.value if hasattr(my_status, 'value') else my_status

    return MatchDetail(
        id=match.id,
        partner=_user_to_public(partner),
        compatibility_score=match.compatibility_score,
        dimension_scores={
            "voice": match.voice_score,
            "face": match.face_score,
            "personality": match.personality_score,
            "values": match.values_score,
            "health": match.health_score,
            "lifestyle": match.lifestyle_score,
        },
        status=status_val,
        is_mutual=match.is_mutual,
        created_at=match.created_at,
    )

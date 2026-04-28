"""
Minder AI 红娘 - AI顾问路由

提供AI红娘对话、约会建议、深度匹配分析等功能。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minder.db import get_db, User
from minder.schemas import (
    AIChatRequest, AIChatResponse,
    DateTipsRequest, DateTipsResponse,
    AnalyzeMatchRequest, AnalyzeMatchResponse,
    ErrorResponse
)
from minder.api.routers.auth import get_current_user
from minder.api.services.ai_service import (
    chat_with_advisor, generate_date_advice,
    deep_analyze_match, ChatContext
)

router = APIRouter(prefix="/ai", tags=["AI红娘"])


@router.post("/chat", response_model=AIChatResponse, summary="与AI红娘对话")
async def ai_chat(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    与AI红娘进行对话。

    AI红娘可以:
    - 解答婚恋问题
    - 提供约会建议
    - 分析匹配情况
    - 给出情感指导

    消息限制: 最长2000字
    """
    context = ChatContext(
        user_profile={
            "id": current_user.id,
            "nickname": current_user.nickname,
            "gender": current_user.gender.value if hasattr(current_user.gender, 'value') else current_user.gender,
            "personality_tags": current_user.personality_tags or [],
            "lifestyle_tags": current_user.lifestyle_tags or [],
        },
        topic=req.context,
    )

    result = await chat_with_advisor(req.message, context)

    return AIChatResponse(
        reply=result["reply"],
        suggestions=result.get("suggestions", []),
    )


@router.get("/date-tips", response_model=DateTipsResponse, summary="获取约会建议")
async def get_date_tips(
    match_user_id: int = Query(None, description="匹配对象ID"),
    scenario: str = Query(None, description="约会场景: 咖啡/美食/户外/文化/运动"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取个性化约会建议。

    基于双方的性格、兴趣等信息, 生成量身定制的约会方案。
    """
    match_user = None
    if match_user_id:
        result = await db.execute(
            select(User).where(User.id == match_user_id, User.is_active == True)
        )
        match_user = result.scalar_one_or_none()
        if not match_user:
            raise HTTPException(status_code=404, detail="用户不存在")

    advice = await generate_date_advice(current_user, match_user, scenario)

    return DateTipsResponse(
        tips=advice["tips"],
        venue_suggestions=advice["venue_suggestions"],
        conversation_starters=advice["conversation_starters"],
    )


@router.post("/analyze-match", response_model=AnalyzeMatchResponse, summary="深度匹配分析")
async def analyze_match(
    req: AnalyzeMatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对指定匹配对象进行深度分析。

    返回综合兼容性评分、各维度分析、优势、顾虑和建议。
    VIP功能。
    """
    if req.target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能分析自己")

    result = await db.execute(
        select(User).where(User.id == req.target_user_id, User.is_active == True)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    analysis = await deep_analyze_match(db, current_user, target_user)

    return AnalyzeMatchResponse(
        overall_score=analysis["overall_score"],
        dimension_scores=analysis["dimension_scores"],
        strengths=analysis["strengths"],
        concerns=analysis["concerns"],
        advice=analysis["advice"],
    )

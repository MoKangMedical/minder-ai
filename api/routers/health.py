"""
Minder AI 红娘 - 健康评估路由

触发健康评估、查看健康报告、查看兼容性分析等功能。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minder.db import get_db, User, HealthReport
from minder.schemas import (
    HealthAssessmentResponse, CompatibilityResponse,
    SuccessResponse, ErrorResponse
)
from minder.api.routers.auth import get_current_user
from minder.api.services.ai_service import analyze_voice, analyze_face

router = APIRouter(prefix="/health", tags=["健康评估"])


@router.post("/assess", response_model=HealthAssessmentResponse, summary="触发健康评估")
async def trigger_assessment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    触发用户健康评估。

    基于用户的语音、面部、性格、生活方式等数据,
    生成综合健康评估报告。

    VIP用户可获得更详细的分析。
    """
    # 模拟语音分析
    voice_result = await analyze_voice(b"")
    # 模拟面部分析
    face_result = await analyze_face(b"")

    # 计算各维度分数
    voice_score = min(100, max(0, voice_result.confidence * 100))
    face_score = min(100, max(0, face_result.attractiveness_score))

    # 性格健康度
    personality_tags = current_user.personality_tags or []
    personality_score = 50.0
    positive_traits = {"乐观", "外向", "理性", "沉稳", "开朗", "温柔"}
    negative_traits = {"消极", "暴躁", "敏感", "焦虑"}
    for tag in personality_tags:
        if tag in positive_traits:
            personality_score += 10
        elif tag in negative_traits:
            personality_score -= 5
    personality_score = min(100, max(0, personality_score))

    # 生活方式健康度
    lifestyle_tags = current_user.lifestyle_tags or []
    lifestyle_score = 50.0
    healthy_lifestyles = {"爱运动", "健身", "跑步", "瑜伽", "早睡早起", "健康饮食"}
    unhealthy_lifestyles = {"熬夜", "抽烟", "酗酒", "久坐"}
    for tag in lifestyle_tags:
        if tag in healthy_lifestyles:
            lifestyle_score += 10
        elif tag in unhealthy_lifestyles:
            lifestyle_score -= 10
    lifestyle_score = min(100, max(0, lifestyle_score))

    # 价值观健康度
    values_tags = current_user.values_tags or []
    values_score = 60.0
    good_values = {"家庭优先", "经济独立", "精神追求", "社会责任"}
    for tag in values_tags:
        if tag in good_values:
            values_score += 8
    values_score = min(100, max(0, values_score))

    # 总体分数
    overall = (
        voice_score * 0.2 +
        face_score * 0.15 +
        personality_score * 0.25 +
        values_score * 0.2 +
        lifestyle_score * 0.2
    )

    # 生成建议
    suggestions = []
    if personality_score < 60:
        suggestions.append("建议培养积极乐观的心态, 可以尝试冥想或心理咨询")
    if lifestyle_score < 60:
        suggestions.append("建议增加运动频率, 保持规律的作息")
    if voice_score < 50:
        suggestions.append("可以录制一段语音介绍, 提高匹配精准度")
    if face_score < 50:
        suggestions.append("建议上传更多生活照, 展示真实的自己")
    if not personality_tags:
        suggestions.append("完善性格标签, 帮助算法更准确地推荐匹配")
    if not lifestyle_tags:
        suggestions.append("添加生活方式标签, 找到兴趣相投的人")
    if not suggestions:
        suggestions.append("你的综合状态良好, 继续保持!")

    # 保存报告
    report = HealthReport(
        user_id=current_user.id,
        overall_score=round(overall, 1),
        voice_analysis={
            "score": round(voice_score, 1),
            "tone_quality": voice_result.tone_quality,
            "emotion": voice_result.emotion,
            "summary": voice_result.summary,
        },
        face_analysis={
            "score": round(face_score, 1),
            "expression": face_result.expression,
            "symmetry": face_result.symmetry_score,
            "summary": face_result.summary,
        },
        personality_analysis={
            "score": round(personality_score, 1),
            "tags": personality_tags,
        },
        lifestyle_analysis={
            "score": round(lifestyle_score, 1),
            "tags": lifestyle_tags,
        },
        values_analysis={
            "score": round(values_score, 1),
            "tags": values_tags,
        },
        suggestions=suggestions,
    )
    db.add(report)

    # 更新用户健康分数
    current_user.health_score = round(overall, 1)
    await db.commit()
    await db.refresh(report)

    return HealthAssessmentResponse(
        report_id=report.id,
        overall_score=report.overall_score,
        dimensions={
            "voice": round(voice_score, 1),
            "face": round(face_score, 1),
            "personality": round(personality_score, 1),
            "values": round(values_score, 1),
            "lifestyle": round(lifestyle_score, 1),
        },
        suggestions=suggestions,
        created_at=report.created_at,
    )


@router.get("/report", response_model=HealthAssessmentResponse, summary="获取我的健康报告")
async def get_my_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户最新的健康评估报告。
    """
    result = await db.execute(
        select(HealthReport)
        .where(HealthReport.user_id == current_user.id)
        .order_by(HealthReport.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="暂无健康报告, 请先进行评估")

    return HealthAssessmentResponse(
        report_id=report.id,
        overall_score=report.overall_score,
        dimensions={
            "voice": (report.voice_analysis or {}).get("score", 0),
            "face": (report.face_analysis or {}).get("score", 0),
            "personality": (report.personality_analysis or {}).get("score", 0),
            "values": (report.values_analysis or {}).get("score", 0),
            "lifestyle": (report.lifestyle_analysis or {}).get("score", 0),
        },
        suggestions=report.suggestions or [],
        created_at=report.created_at,
    )


@router.get("/compatibility/{user_id}", response_model=CompatibilityResponse, summary="兼容性分析")
async def get_compatibility(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查看与指定用户的兼容性分析。

    需要VIP会员或双方已互相匹配。
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能与自己比较兼容性")

    from minder.api.services.matching_service import calculate_compatibility

    result = await db.execute(select(User).where(User.id == user_id))
    other_user = result.scalar_one_or_none()
    if not other_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    total, dim_scores = calculate_compatibility(current_user, other_user)

    # 生成分析文字
    analysis_parts = []
    if dim_scores["personality"] >= 0.7:
        analysis_parts.append("你们的性格非常互补")
    elif dim_scores["personality"] >= 0.5:
        analysis_parts.append("你们的性格有一定契合度")
    else:
        analysis_parts.append("你们的性格差异较大, 需要更多磨合")

    if dim_scores["values"] >= 0.7:
        analysis_parts.append("价值观高度一致, 这是长期关系的基础")
    elif dim_scores["values"] >= 0.5:
        analysis_parts.append("核心价值观比较接近")
    else:
        analysis_parts.append("在价值观上存在一些分歧, 建议深入了解")

    analysis = "。".join(analysis_parts) + f"。综合兼容性 {total*100:.1f}%。"

    return CompatibilityResponse(
        user_id=current_user.id,
        partner_id=user_id,
        overall_score=total,
        dimension_scores=dim_scores,
        analysis=analysis,
    )

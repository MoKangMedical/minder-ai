"""
Minder AI 红娘 - 支付/订阅路由

处理套餐查看、订阅、取消订阅、查询订阅状态等功能。
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from minder.db import get_db, User, SubscriptionTier
from minder.schemas import (
    PlanInfo, SubscribeRequest, SubscriptionStatus,
    SuccessResponse, ErrorResponse
)
from minder.api.routers.auth import get_current_user
from minder.api.services.payment_service import (
    get_all_plans, create_subscription, cancel_subscription,
    check_subscription_status
)

router = APIRouter(prefix="/payments", tags=["支付订阅"])


@router.get("/plans", response_model=List[PlanInfo], summary="获取套餐列表")
async def list_plans():
    """
    获取所有可用的订阅套餐。

    包含免费版、基础会员、VIP会员、超级VIP。
    """
    plans = await get_all_plans()
    return [
        PlanInfo(
            tier=p["tier"],
            name=p["name"],
            price=p["price"],
            duration_days=p["duration_days"],
            features=p["features"],
        )
        for p in plans
    ]


@router.post("/subscribe", response_model=SuccessResponse, summary="订阅套餐")
async def subscribe(
    req: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    订阅指定套餐。

    支持支付宝、微信支付、Apple Pay。
    """
    tier_map = {
        "basic": SubscriptionTier.BASIC,
        "vip": SubscriptionTier.VIP,
        "svip": SubscriptionTier.SVIP,
    }
    tier = tier_map.get(req.tier)
    if not tier:
        raise HTTPException(
            status_code=400,
            detail="无效的套餐等级, 可选: basic/vip/svip"
        )

    success, message, subscription = await create_subscription(
        db, current_user.id, tier, req.payment_method
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return SuccessResponse(
        message=message,
        data={
            "tier": req.tier,
            "expires_at": subscription.expires_at.isoformat() if subscription else None,
        }
    )


@router.post("/cancel-subscription", response_model=SuccessResponse, summary="取消订阅")
async def cancel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消当前订阅。

    取消后可以使用到当前周期结束。
    """
    success, message = await cancel_subscription(db, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return SuccessResponse(message=message)


@router.get("/subscription-status", response_model=SubscriptionStatus, summary="查询订阅状态")
async def subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询当前用户的订阅状态。

    包含套餐等级、是否有效、到期时间、剩余天数等信息。
    """
    status = await check_subscription_status(db, current_user.id)
    return SubscriptionStatus(
        tier=status["tier"],
        is_active=status["is_active"],
        started_at=None,
        expires_at=status.get("expires_at"),
        days_remaining=status.get("days_remaining", 0),
    )

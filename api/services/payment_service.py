"""
Minder AI 红娘 - 支付/订阅服务

管理用户订阅、套餐、支付等功能。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minder.db.models import (
    User, Subscription, SubscriptionTier
)


# ==================== 套餐配置 ====================

PLANS = {
    SubscriptionTier.FREE: {
        "tier": "free",
        "name": "免费版",
        "price": 0.0,
        "duration_days": 0,
        "features": [
            "每日推荐5位匹配对象",
            "基础匹配算法",
            "每日发送3条消息",
            "浏览公开资料",
        ],
    },
    SubscriptionTier.BASIC: {
        "tier": "basic",
        "name": "基础会员",
        "price": 29.9,
        "duration_days": 30,
        "features": [
            "每日推荐15位匹配对象",
            "高级匹配算法",
            "无限消息发送",
            "查看谁喜欢了你",
            "语音分析解锁",
        ],
    },
    SubscriptionTier.VIP: {
        "tier": "vip",
        "name": "VIP会员",
        "price": 68.0,
        "duration_days": 30,
        "features": [
            "每日推荐30位匹配对象",
            "全部高级功能",
            "AI红娘深度分析",
            "优先展示",
            "已读回执",
            "隐身浏览",
        ],
    },
    SubscriptionTier.SVIP: {
        "tier": "svip",
        "name": "超级VIP",
        "price": 128.0,
        "duration_days": 30,
        "features": [
            "无限推荐匹配对象",
            "所有VIP功能",
            "专属红娘服务",
            "优先客服",
            "线下活动邀请",
            "资料置顶",
        ],
    },
}


async def get_all_plans() -> List[Dict]:
    """获取所有套餐信息"""
    return [PLANS[tier] for tier in SubscriptionTier]


async def create_subscription(
    db: AsyncSession,
    user_id: int,
    tier: SubscriptionTier,
    payment_method: str = "alipay"
) -> Tuple[bool, str, Optional[Subscription]]:
    """
    创建订阅。

    Args:
        db: 数据库会话
        user_id: 用户ID
        tier: 套餐等级
        payment_method: 支付方式

    Returns:
        (success, message, subscription)
    """
    # 获取用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False, "用户不存在", None

    # 检查是否已有活跃订阅
    if user.subscription_tier != SubscriptionTier.FREE:
        if user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow():
            return False, "您已有活跃订阅, 请先取消或等待过期", None

    # 获取套餐信息
    plan = PLANS.get(tier)
    if not plan or plan["price"] == 0:
        return False, "无效的套餐", None

    # 模拟支付处理
    # 生产环境中, 这里会调用支付宝/微信支付API
    payment_success = await _process_payment(
        amount=plan["price"],
        method=payment_method,
        user_id=user_id,
    )

    if not payment_success:
        return False, "支付失败, 请重试", None

    # 创建订阅记录
    now = datetime.utcnow()
    expires_at = now + timedelta(days=plan["duration_days"])

    subscription = Subscription(
        user_id=user_id,
        tier=tier,
        started_at=now,
        expires_at=expires_at,
        is_active=True,
        payment_id=f"PAY_{user_id}_{int(now.timestamp())}",
        amount=plan["price"],
    )
    db.add(subscription)

    # 更新用户订阅状态
    user.subscription_tier = tier
    user.subscription_expires_at = expires_at

    await db.commit()
    await db.refresh(subscription)

    return True, "订阅成功", subscription


async def cancel_subscription(
    db: AsyncSession,
    user_id: int
) -> Tuple[bool, str]:
    """
    取消订阅。

    取消后, 用户可以在当前周期结束前继续使用。
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False, "用户不存在"

    if user.subscription_tier == SubscriptionTier.FREE:
        return False, "您当前没有活跃订阅"

    # 查找活跃订阅
    stmt = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.is_active == True
    ).order_by(Subscription.created_at.desc())
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.is_active = False
        await db.commit()

    # 不立即降级, 到期后自动降级
    return True, "订阅已取消, 您可以使用到当前周期结束"


async def check_subscription_status(
    db: AsyncSession,
    user_id: int
) -> Dict:
    """
    检查用户订阅状态。

    如果订阅已过期, 自动降级为免费版。
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"tier": "free", "is_active": False, "error": "用户不存在"}

    now = datetime.utcnow()

    # 检查是否过期
    if (user.subscription_tier != SubscriptionTier.FREE and
            user.subscription_expires_at and
            user.subscription_expires_at <= now):
        # 自动降级
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_expires_at = None
        await db.commit()

    is_active = (
        user.subscription_tier != SubscriptionTier.FREE and
        user.subscription_expires_at is not None and
        user.subscription_expires_at > now
    )

    days_remaining = 0
    if is_active and user.subscription_expires_at:
        days_remaining = (user.subscription_expires_at - now).days

    plan = PLANS.get(user.subscription_tier, PLANS[SubscriptionTier.FREE])

    return {
        "tier": user.subscription_tier.value if isinstance(user.subscription_tier, SubscriptionTier) else user.subscription_tier,
        "name": plan["name"],
        "is_active": is_active,
        "started_at": None,  # 可从subscription记录获取
        "expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "days_remaining": days_remaining,
        "features": plan["features"],
    }


async def _process_payment(
    amount: float,
    method: str,
    user_id: int
) -> bool:
    """
    处理支付 (模拟)。

    生产环境中对接真实支付网关:
    - 支付宝 (alipay)
    - 微信支付 (wechat)
    - Apple Pay (apple)
    """
    # 模拟支付成功
    return True

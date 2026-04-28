"""
Minder AI 红娘 - 举报路由

处理用户举报和管理员查看举报列表等功能。
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minder.db import get_db, User, Report, ReportReason
from minder.schemas import (
    ReportCreate, ReportResponse,
    SuccessResponse, ErrorResponse
)
from minder.api.routers.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["举报"])


@router.post("/report", response_model=SuccessResponse, summary="举报用户")
async def report_user(
    req: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    举报用户。

    可选举报原因:
    - fake_profile: 虚假资料
    - harassment: 骚扰行为
    - inappropriate: 不当内容
    - spam: 垃圾信息
    - other: 其他
    """
    if req.reported_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能举报自己")

    # 验证被举报用户存在
    result = await db.execute(
        select(User).where(User.id == req.reported_user_id)
    )
    reported_user = result.scalar_one_or_none()
    if not reported_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否重复举报
    result = await db.execute(
        select(Report).where(
            Report.reporter_id == current_user.id,
            Report.reported_user_id == req.reported_user_id,
            Report.is_resolved == False
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="您已举报过该用户, 正在处理中")

    reason_map = {
        "fake_profile": ReportReason.FAKE_PROFILE,
        "harassment": ReportReason.HARASSMENT,
        "inappropriate": ReportReason.INAPPROPRIATE,
        "spam": ReportReason.SPAM,
        "other": ReportReason.OTHER,
    }
    reason = reason_map.get(req.reason)
    if not reason:
        raise HTTPException(
            status_code=400,
            detail="无效的举报原因, 可选: fake_profile/harassment/inappropriate/spam/other"
        )

    report = Report(
        reporter_id=current_user.id,
        reported_user_id=req.reported_user_id,
        reason=reason,
        description=req.description,
    )
    db.add(report)
    await db.commit()

    return SuccessResponse(
        message="举报已提交, 我们会尽快处理",
        data={"report_id": report.id}
    )


@router.get("/reports", response_model=List[ReportResponse], summary="举报列表 (管理员)")
async def list_reports(
    is_resolved: bool = Query(False, description="筛选已处理/未处理"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取举报列表 (管理员功能)。

    注意: 生产环境中需要添加管理员权限验证。
    当前简化实现允许所有登录用户查看。
    """
    # TODO: 添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理员权限")

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Report)
        .where(Report.is_resolved == is_resolved)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reports = result.scalars().all()

    return [
        ReportResponse(
            id=r.id,
            reporter_id=r.reporter_id,
            reported_user_id=r.reported_user_id,
            reason=r.reason.value if hasattr(r.reason, 'value') else r.reason,
            description=r.description,
            is_resolved=r.is_resolved,
            created_at=r.created_at,
        )
        for r in reports
    ]

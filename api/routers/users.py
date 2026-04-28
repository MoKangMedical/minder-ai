"""
Minder AI 红娘 - 用户管理路由

处理用户资料查看、编辑、照片管理等功能。
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from minder.db import get_db, User, UserPhoto, Gender
from minder.schemas import (
    UserPublicProfile, UserFullProfile, UserProfileUpdate,
    PhotoResponse, SuccessResponse, ErrorResponse
)
from minder.api.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["用户"])


def _age_from_birth(birth_date: datetime) -> int:
    """计算年龄"""
    today = datetime.utcnow()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def _user_to_public(user: User) -> UserPublicProfile:
    """转换为公开资料"""
    return UserPublicProfile(
        id=user.id,
        nickname=user.nickname,
        gender=user.gender.value if isinstance(user.gender, Gender) else user.gender,
        age=_age_from_birth(user.birth_date),
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
    )


def _user_to_full(user: User) -> UserFullProfile:
    """转换为完整资料"""
    pub = _user_to_public(user)
    return UserFullProfile(
        **pub.model_dump(),
        phone=user.phone[:3] + "****" + user.phone[-4:],
        preferred_gender=user.preferred_gender.value if user.preferred_gender else None,
        preferred_age_min=user.preferred_age_min,
        preferred_age_max=user.preferred_age_max,
        preferred_city=user.preferred_city,
        subscription_tier=user.subscription_tier.value if hasattr(user.subscription_tier, 'value') else user.subscription_tier,
        health_score=user.health_score,
        created_at=user.created_at or datetime.utcnow(),
    )


@router.get("/me", response_model=UserFullProfile, summary="获取我的资料")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户的完整个人资料。
    """
    result = await db.execute(
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.photos))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _user_to_full(user)


@router.put("/me", response_model=SuccessResponse, summary="更新我的资料")
async def update_my_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的个人资料。
    只更新传入的字段, 未传入的字段保持不变。
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = update.model_dump(exclude_unset=True)

    # 字段映射和验证
    string_fields = {"nickname", "bio", "city", "occupation", "education", "preferred_city"}
    int_fields = {"height_cm", "preferred_age_min", "preferred_age_max"}
    list_fields = {"personality_tags", "values_tags", "lifestyle_tags"}

    for field_name, value in update_data.items():
        if field_name in string_fields:
            setattr(user, field_name, value)
        elif field_name in int_fields:
            if value is not None:
                setattr(user, field_name, value)
        elif field_name in list_fields:
            setattr(user, field_name, value)
        elif field_name == "preferred_gender":
            if value:
                gender_map = {"male": Gender.MALE, "female": Gender.FEMALE, "other": Gender.OTHER}
                user.preferred_gender = gender_map.get(value)

    user.updated_at = datetime.utcnow()
    await db.commit()

    return SuccessResponse(message="资料更新成功")


@router.get("/{user_id}", response_model=UserPublicProfile, summary="查看用户公开资料")
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查看指定用户的公开资料。
    不能查看自己的资料 (请使用 /me)。
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="请使用 /me 查看自己的资料")

    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.is_active == True)
        .options(selectinload(User.photos))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return _user_to_public(user)


@router.post("/me/photos", response_model=PhotoResponse, summary="上传照片")
async def upload_photo(
    url: str,
    is_primary: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传用户照片。

    参数:
    - url: 照片URL (实际生产中通过文件上传接口获取)
    - is_primary: 是否设为头像

    每个用户最多上传9张照片。
    """
    # 检查照片数量限制
    result = await db.execute(
        select(UserPhoto).where(UserPhoto.user_id == current_user.id)
    )
    existing_photos = result.scalars().all()
    if len(existing_photos) >= 9:
        raise HTTPException(status_code=400, detail="最多只能上传9张照片")

    # 如果设为头像, 取消其他头像
    if is_primary:
        for photo in existing_photos:
            photo.is_primary = False

    # 确定排序
    max_order = max([p.order for p in existing_photos], default=-1)

    photo = UserPhoto(
        user_id=current_user.id,
        url=url,
        is_primary=is_primary or len(existing_photos) == 0,
        order=max_order + 1,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return PhotoResponse(
        id=photo.id,
        url=photo.url,
        is_primary=photo.is_primary,
        order=photo.order,
    )


@router.delete("/me/photos/{photo_id}", response_model=SuccessResponse, summary="删除照片")
async def delete_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定照片。
    """
    result = await db.execute(
        select(UserPhoto).where(
            UserPhoto.id == photo_id,
            UserPhoto.user_id == current_user.id
        )
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    was_primary = photo.is_primary
    await db.delete(photo)
    await db.commit()

    # 如果删除的是头像, 将第一张设为头像
    if was_primary:
        result = await db.execute(
            select(UserPhoto)
            .where(UserPhoto.user_id == current_user.id)
            .order_by(UserPhoto.order)
        )
        first_photo = result.scalars().first()
        if first_photo:
            first_photo.is_primary = True
            await db.commit()

    return SuccessResponse(message="照片已删除")

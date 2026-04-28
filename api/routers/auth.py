"""
Minder AI 红娘 - 认证路由

处理用户注册、登录、令牌刷新、登出等认证相关功能。
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minder.db import get_db, User, Gender
from minder.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshTokenRequest, SuccessResponse, ErrorResponse
)

router = APIRouter(prefix="/auth", tags=["认证"])

# JWT 密钥 (生产环境使用环境变量)
SECRET_KEY = "minder-ai-matchmaking-secret-key-2024"
REFRESH_SECRET_KEY = "minder-ai-refresh-secret-key-2024"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

# 简化的JWT实现 (生产环境使用python-jose)
import base64
import json


def _create_token(data: dict, secret: str, expires_delta: timedelta) -> str:
    """创建简化JWT令牌"""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload_data = {
        **data,
        "exp": int((datetime.utcnow() + expires_delta).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    signature_input = f"{header}.{payload}.{secret}"
    signature = hashlib.sha256(signature_input.encode()).hexdigest()[:32]
    return f"{header}.{payload}.{signature}"


def _verify_token(token: str, secret: str) -> Optional[dict]:
    """验证令牌"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        signature_input = f"{header}.{payload}.{secret}"
        expected_sig = hashlib.sha256(signature_input.encode()).hexdigest()[:32]
        if signature != expected_sig:
            return None
        # 补齐base64填充
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        data = json.loads(base64.urlsafe_b64decode(payload))
        if data.get("exp", 0) < datetime.utcnow().timestamp():
            return None
        return data
    except Exception:
        return None


def _hash_password(password: str) -> str:
    """密码哈希"""
    salt = "minder_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return _hash_password(password) == password_hash


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """从Authorization header获取当前用户"""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif authorization:
        token = authorization
    
    if not token:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    payload = _verify_token(token, SECRET_KEY)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌数据")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

    return user


@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册

    通过手机号和短信验证码注册新用户。
    注册成功后返回访问令牌。
    """
    # 验证短信验证码 (模拟)
    if req.sms_code != "888888":
        raise HTTPException(
            status_code=400,
            detail="短信验证码错误"
        )

    # 检查手机号是否已注册
    result = await db.execute(select(User).where(User.phone == req.phone))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="该手机号已注册"
        )

    # 创建用户
    try:
        birth_date = datetime.strptime(req.birth_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="出生日期格式错误, 请使用YYYY-MM-DD")

    gender_map = {"male": Gender.MALE, "female": Gender.FEMALE, "other": Gender.OTHER}
    gender = gender_map.get(req.gender)
    if not gender:
        raise HTTPException(status_code=400, detail="性别值无效, 可选: male/female/other")

    user = User(
        phone=req.phone,
        password_hash=_hash_password(req.password),
        nickname=req.nickname,
        gender=gender,
        birth_date=birth_date,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成令牌
    access_token = _create_token(
        {"user_id": user.id, "phone": user.phone},
        SECRET_KEY,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = _create_token(
        {"user_id": user.id, "type": "refresh"},
        REFRESH_SECRET_KEY,
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录

    通过手机号和密码登录, 返回访问令牌。
    """
    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()

    if not user or not _verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="手机号或密码错误"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="账号已被禁用, 请联系客服"
        )

    access_token = _create_token(
        {"user_id": user.id, "phone": user.phone},
        SECRET_KEY,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = _create_token(
        {"user_id": user.id, "type": "refresh"},
        REFRESH_SECRET_KEY,
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh-token", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    刷新访问令牌

    使用刷新令牌获取新的访问令牌。
    """
    payload = _verify_token(req.refresh_token, REFRESH_SECRET_KEY)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="无效或过期的刷新令牌"
        )

    user_id = payload.get("user_id")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="用户不存在或已被禁用"
        )

    access_token = _create_token(
        {"user_id": user.id, "phone": user.phone},
        SECRET_KEY,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = _create_token(
        {"user_id": user.id, "type": "refresh"},
        REFRESH_SECRET_KEY,
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=SuccessResponse, summary="用户登出")
async def logout():
    """
    用户登出

    客户端应自行清除令牌。
    服务端可维护令牌黑名单 (当前简化实现)。
    """
    return SuccessResponse(message="登出成功")


@router.post("/sms/send", response_model=SuccessResponse, summary="发送短信验证码")
async def send_sms_code(phone: str, db: AsyncSession = Depends(get_db)):
    """
    发送短信验证码

    模拟实现: 固定返回888888
    生产环境对接短信服务商API
    """
    # 验证手机号格式
    import re
    if not re.match(r"^1[3-9]\d{9}$", phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    # 模拟发送短信
    return SuccessResponse(message="验证码已发送", data={"code": "888888"})

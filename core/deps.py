"""
Minder AI红娘平台 - 依赖注入
提供FastAPI路由所需的公共依赖项
"""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from minder.core.database import async_session_factory
from minder.core.security import decode_token

# HTTP Bearer认证方案
security_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库异步会话（FastAPI依赖项）
    每个请求一个独立会话，请求结束后自动关闭
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> UUID:
    """
    从JWT令牌中提取当前用户ID
    :param credentials: HTTP Bearer认证凭据
    :return: 当前用户的UUID
    :raises HTTPException: 令牌无效或过期
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误，请使用访问令牌",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌中缺少用户信息",
        )

    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户ID格式无效",
        )


async def get_current_active_user_id(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    获取当前活跃用户ID（验证用户是否被禁用）
    :param user_id: 当前用户UUID
    :param db: 数据库会话
    :return: 活跃用户的UUID
    :raises HTTPException: 用户不存在或已被禁用
    """
    from minder.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用",
        )

    return user_id


async def get_current_vip_user(
    user_id: UUID = Depends(get_current_active_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    获取当前VIP用户ID（验证用户是否有VIP权限）
    :param user_id: 当前活跃用户UUID
    :param db: 数据库会话
    :return: VIP用户的UUID
    :raises HTTPException: 用户不是VIP
    """
    from minder.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or user.vip_level < 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此功能仅限VIP会员使用",
        )

    return user_id

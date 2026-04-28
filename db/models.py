"""
Minder AI 红娘 - 数据模型定义

定义用户、匹配、消息、订阅等核心数据模型。
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, Enum,
    ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./minder.db"


class Base(DeclarativeBase):
    pass


# ---------- 枚举 ----------

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    VIP = "vip"
    SVIP = "svip"


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ReportReason(str, enum.Enum):
    FAKE_PROFILE = "fake_profile"
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"
    SPAM = "spam"
    OTHER = "other"


# ---------- 用户 ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    nickname = Column(String(50), nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    birth_date = Column(DateTime, nullable=False)
    city = Column(String(50))
    bio = Column(Text, default="")
    occupation = Column(String(100))
    education = Column(String(100))
    height_cm = Column(Integer)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    # 个人偏好
    preferred_gender = Column(Enum(Gender), nullable=True)
    preferred_age_min = Column(Integer, default=18)
    preferred_age_max = Column(Integer, default=60)
    preferred_city = Column(String(50), nullable=True)
    # 性格 / 价值观 (JSON)
    personality_tags = Column(JSON, default=list)       # e.g. ["外向","乐观","理性"]
    values_tags = Column(JSON, default=list)             # e.g. ["家庭优先","事业心强"]
    lifestyle_tags = Column(JSON, default=list)          # e.g. ["爱运动","宅","旅行"]
    # 健康数据
    health_score = Column(Float, default=0.0)            # 0-100
    # AI 分析缓存
    voice_embedding = Column(JSON, nullable=True)
    face_embedding = Column(JSON, nullable=True)
    personality_vector = Column(JSON, nullable=True)
    values_vector = Column(JSON, nullable=True)
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    photos = relationship("UserPhoto", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    health_reports = relationship("HealthReport", back_populates="user", cascade="all, delete-orphan")


class UserPhoto(Base):
    __tablename__ = "user_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="photos")


# ---------- 匹配 ----------

class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_match_pair"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    compatibility_score = Column(Float, default=0.0)
    # 维度得分
    voice_score = Column(Float, default=0.0)
    face_score = Column(Float, default=0.0)
    personality_score = Column(Float, default=0.0)
    values_score = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)
    lifestyle_score = Column(Float, default=0.0)
    status_a = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    status_b = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    is_mutual = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])


# ---------- 消息 ----------

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text / image / voice
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    match = relationship("Match")


# ---------- 健康报告 ----------

class HealthReport(Base):
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    overall_score = Column(Float, default=0.0)
    voice_analysis = Column(JSON, nullable=True)
    face_analysis = Column(JSON, nullable=True)
    personality_analysis = Column(JSON, nullable=True)
    lifestyle_analysis = Column(JSON, nullable=True)
    values_analysis = Column(JSON, nullable=True)
    suggestions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_reports")


# ---------- 订阅 / 支付 ----------

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tier = Column(Enum(SubscriptionTier), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    payment_id = Column(String(100), nullable=True)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- 举报 ----------

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Enum(ReportReason), nullable=False)
    description = Column(Text, default="")
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- 数据库引擎 ----------

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """获取数据库会话 (FastAPI Depends)"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

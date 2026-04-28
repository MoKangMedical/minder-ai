"""
Minder AI 红娘 - 统一 Pydantic 数据模型

所有 API 请求/响应模型集中定义。
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 通用响应 ====================

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: str = ""

class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: str = ""
    data: Optional[dict] = None


# ==================== 认证 ====================

class RegisterRequest(BaseModel):
    """注册请求"""
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    nickname: str = Field(..., min_length=1, max_length=50, description="昵称")
    gender: str = Field(..., description="性别: male/female/other")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    sms_code: str = Field("888888", description="短信验证码")

class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")

class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


# ==================== 用户 ====================

class UserPublicProfile(BaseModel):
    """用户公开资料（他人可见）"""
    id: int
    nickname: str
    gender: str
    age: int
    city: Optional[str] = None
    bio: str = ""
    occupation: Optional[str] = None
    education: Optional[str] = None
    height_cm: Optional[int] = None
    avatar_url: Optional[str] = None
    personality_tags: List[str] = []
    values_tags: List[str] = []
    lifestyle_tags: List[str] = []
    is_verified: bool = False

class UserFullProfile(UserPublicProfile):
    """用户完整资料（本人可见）"""
    phone: str
    preferred_gender: Optional[str] = None
    preferred_age_min: int = 18
    preferred_age_max: int = 60
    preferred_city: Optional[str] = None
    subscription_tier: str = "free"
    subscription_expires_at: Optional[datetime] = None
    health_score: float = 0.0
    created_at: datetime

class UserProfileUpdate(BaseModel):
    """资料更新请求"""
    nickname: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    height_cm: Optional[int] = None
    avatar_url: Optional[str] = None
    personality_tags: Optional[List[str]] = None
    values_tags: Optional[List[str]] = None
    lifestyle_tags: Optional[List[str]] = None
    preferred_gender: Optional[str] = None
    preferred_age_min: Optional[int] = None
    preferred_age_max: Optional[int] = None
    preferred_city: Optional[str] = None

class PhotoResponse(BaseModel):
    """照片响应"""
    id: int
    url: str
    is_primary: bool = False
    order: int = 0
    created_at: datetime


# ==================== 匹配 ====================

class MatchCandidate(BaseModel):
    """匹配候选人"""
    user: UserPublicProfile
    compatibility_score: float = Field(..., description="综合匹配度 0-100")
    voice_score: float = 0.0
    face_score: float = 0.0
    personality_score: float = 0.0
    values_score: float = 0.0
    health_score: float = 0.0
    lifestyle_score: float = 0.0
    ai_reason: str = Field("", description="AI推荐理由")

class DiscoverResponse(BaseModel):
    """发现页响应"""
    candidates: List[MatchCandidate]
    total: int
    page: int = 1
    page_size: int = 10
    has_more: bool = False

class MatchDetail(BaseModel):
    """匹配详情"""
    id: int
    user: UserPublicProfile
    compatibility_score: float
    voice_score: float = 0.0
    face_score: float = 0.0
    personality_score: float = 0.0
    values_score: float = 0.0
    health_score: float = 0.0
    lifestyle_score: float = 0.0
    status: str
    is_mutual: bool = False
    ai_reason: str = ""
    created_at: datetime

class MatchAction(BaseModel):
    """匹配操作"""
    action: str = Field(..., description="accept/reject")


# ==================== 消息 ====================

class MessageCreate(BaseModel):
    """发送消息"""
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")
    message_type: str = Field("text", description="text/image/voice")

class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    match_id: int
    sender_id: int
    sender_nickname: str = ""
    content: str
    message_type: str = "text"
    is_read: bool = False
    created_at: datetime

class ConversationSummary(BaseModel):
    """会话摘要"""
    match_id: int
    partner: UserPublicProfile
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0


# ==================== 健康评估 ====================

class HealthAssessmentResponse(BaseModel):
    """健康评估响应"""
    overall_score: float = Field(..., description="综合健康分 0-100")
    voice_analysis: Optional[dict] = None
    face_analysis: Optional[dict] = None
    personality_analysis: Optional[dict] = None
    lifestyle_analysis: Optional[dict] = None
    values_analysis: Optional[dict] = None
    suggestions: List[str] = []
    created_at: datetime

class CompatibilityResponse(BaseModel):
    """兼容性分析响应"""
    user_id: int
    overall_score: float
    dimension_scores: dict = {}
    ai_summary: str = ""
    suggestions: List[str] = []


# ==================== 支付 / 订阅 ====================

class PlanInfo(BaseModel):
    """套餐信息"""
    plan_id: str = Field("", description="套餐ID")
    tier: str = Field("", description="套餐层级")
    name: str
    price: float
    currency: str = "CNY"
    duration_days: int
    features: List[str] = []

class SubscribeRequest(BaseModel):
    """订阅请求"""
    plan_id: str = Field(..., description="套餐ID: free/vip/svip")
    payment_method: str = Field("wechat", description="支付方式: wechat/alipay/card")

class SubscriptionStatus(BaseModel):
    """订阅状态"""
    tier: str
    is_active: bool = False
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renew: bool = False
    days_remaining: int = 0


# ==================== 举报 ====================

class ReportCreate(BaseModel):
    """举报请求"""
    reported_user_id: int = Field(..., description="被举报用户ID")
    reason: str = Field(..., description="举报原因")
    description: str = Field("", max_length=1000, description="详细描述")

class ReportResponse(BaseModel):
    """举报响应"""
    id: int
    reporter_id: int
    reported_user_id: int
    reason: str
    description: str
    is_resolved: bool = False
    created_at: datetime


# ==================== AI 红娘 ====================

class AIChatRequest(BaseModel):
    """AI红娘对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    context: Optional[dict] = Field(None, description="上下文（当前匹配对象等）")

class AIChatResponse(BaseModel):
    """AI红娘对话响应"""
    reply: str
    suggestions: List[str] = []
    action_hint: Optional[str] = None

class DateTipsRequest(BaseModel):
    """约会建议请求"""
    match_user_id: int = Field(..., description="约会对象ID")
    date_type: str = Field("casual", description="约会类型: casual/formal/outdoor/online")

class DateTipsResponse(BaseModel):
    """约会建议响应"""
    tips: List[str]
    conversation_starters: List[str]
    warning_signs: List[str]
    outfit_suggestion: str = ""

class AnalyzeMatchRequest(BaseModel):
    """深度匹配分析请求"""
    target_user_id: int = Field(..., description="分析对象ID")

class AnalyzeMatchResponse(BaseModel):
    """深度匹配分析响应"""
    overall_score: float
    dimension_breakdown: dict
    strengths: List[str]
    potential_issues: List[str]
    relationship_advice: str
    long_term_prediction: str

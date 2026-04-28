"""
Minder AI红娘平台 - 核心配置
提供全局配置参数，从环境变量或 .env 文件加载
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用全局配置"""

    # ==================== 基础配置 ====================
    APP_NAME: str = "Minder AI红娘平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ==================== 安全配置 ====================
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ==================== 数据库配置 ====================
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/minder"

    # ==================== Redis配置 ====================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==================== AI引擎配置 ====================
    AI_MATCH_ENDPOINT: str = "http://localhost:8001/api/match"
    AI_VOICE_ENDPOINT: str = "http://localhost:8002/api/voice"
    AI_FACE_ENDPOINT: str = "http://localhost:8003/api/face"
    AI_HEALTH_ENDPOINT: str = "http://localhost:8004/api/health"
    AI_PERSONALITY_ENDPOINT: str = "http://localhost:8005/api/personality"

    # ==================== 支付配置 ====================
    WECHAT_PAY_APP_ID: str = ""
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_API_KEY: str = ""
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""

    # ==================== 短信/验证码 ====================
    SMS_ACCESS_KEY: str = ""
    SMS_SECRET_KEY: str = ""
    SMS_SIGN_NAME: str = "Minder红娘"
    SMS_TEMPLATE_CODE: str = ""

    # ==================== 对象存储 (OSS) ====================
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET_NAME: str = "minder-media"

    # ==================== 向量数据库 ====================
    VECTOR_DB_URL: str = "http://localhost:6333"
    VECTOR_DB_COLLECTION: str = "minder_embeddings"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

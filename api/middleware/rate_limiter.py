"""
Minder AI 红娘 - 速率限制中间件

基于内存的请求频率限制:
- 免费用户: 100 次/分钟
- VIP用户: 500 次/分钟
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# 速率限制配置
RATE_LIMITS = {
    "free": {"requests": 100, "window": 60},    # 100 req/min
    "basic": {"requests": 200, "window": 60},    # 200 req/min
    "vip": {"requests": 500, "window": 60},      # 500 req/min
    "svip": {"requests": 1000, "window": 60},    # 1000 req/min
}

# 白名单路径 (不受限制)
WHITELIST_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

# 存储: {client_ip: [(timestamp, path), ...]}
_request_store: Dict[str, list] = defaultdict(list)


def _cleanup_old_records(client_key: str, window: int):
    """清理过期的请求记录"""
    now = time.time()
    cutoff = now - window
    _request_store[client_key] = [
        (ts, path) for ts, path in _request_store[client_key]
        if ts > cutoff
    ]


def _get_client_key(request: Request) -> str:
    """获取客户端标识 (IP 或 user-agent 组合)"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    return ip


def _get_rate_limit(request: Request) -> Tuple[int, int]:
    """获取当前用户的速率限制"""
    # 从请求状态中获取用户订阅等级
    tier = getattr(request.state, "subscription_tier", "free") if hasattr(request, "state") else "free"
    if isinstance(tier, str):
        config = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
    else:
        tier_value = tier.value if hasattr(tier, "value") else "free"
        config = RATE_LIMITS.get(tier_value, RATE_LIMITS["free"])
    return config["requests"], config["window"]


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    async def dispatch(self, request: Request, call_next):
        # 白名单路径跳过
        path = request.url.path
        if any(path.startswith(wp) for wp in WHITELIST_PATHS):
            return await call_next(request)

        client_key = _get_client_key(request)
        max_requests, window = _get_rate_limit(request)

        # 清理旧记录
        _cleanup_old_records(client_key, window)

        # 检查当前窗口内的请求数
        current_count = len(_request_store[client_key])

        if current_count >= max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "请求过于频繁",
                    "detail": f"请在{window}秒后重试",
                    "retry_after": window,
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + window),
                }
            )

        # 记录请求
        _request_store[client_key].append((time.time(), path))

        # 处理请求
        response = await call_next(request)

        # 添加速率限制响应头
        remaining = max(0, max_requests - len(_request_store[client_key]))
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response

"""
Minder AI 红娘 - 安全中间件

提供请求验证、XSS防护、安全头等安全功能。
"""
from __future__ import annotations

import html
import re
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# 安全响应头
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "X-Download-Options": "noopen",
    "X-DNS-Prefetch-Control": "off",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss:;"
    ),
}

# 危险的请求头
BLOCKED_HEADERS = {"x-forwarded-host"}

# XSS 检测模式
XSS_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"<object", re.IGNORECASE),
    re.compile(r"<embed", re.IGNORECASE),
    re.compile(r"<form", re.IGNORECASE),
]

# SQL注入检测模式
SQL_INJECTION_PATTERNS = [
    re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
    re.compile(r"(\bselect\b.*\bfrom\b)", re.IGNORECASE),
    re.compile(r"(\binsert\b.*\binto\b)", re.IGNORECASE),
    re.compile(r"(\bdelete\b.*\bfrom\b)", re.IGNORECASE),
    re.compile(r"(\bdrop\b.*\btable\b)", re.IGNORECASE),
    re.compile(r"('\s*or\s+')", re.IGNORECASE),
    re.compile(r"(--\s*$)", re.IGNORECASE),
]

# 路径遍历检测
PATH_TRAVERSAL_PATTERNS = [
    re.compile(r"\.\./"),
    re.compile(r"\.\.\\"),
    re.compile(r"%2e%2e", re.IGNORECASE),
]


def _check_xss(value: str) -> bool:
    """检查字符串中是否包含XSS攻击模式"""
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _check_sql_injection(value: str) -> bool:
    """检查字符串中是否包含SQL注入模式"""
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _check_path_traversal(value: str) -> bool:
    """检查路径遍历攻击"""
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _sanitize_string(value: str) -> str:
    """清理字符串中的危险内容"""
    # HTML转义
    value = html.escape(value)
    return value


def _scan_request_value(value: str) -> bool:
    """扫描请求值中是否存在安全隐患"""
    if _check_xss(value):
        return True
    if _check_sql_injection(value):
        return True
    if _check_path_traversal(value):
        return True
    return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""

    async def dispatch(self, request: Request, call_next):
        # 1. 检查请求头
        for header_name in BLOCKED_HEADERS:
            if header_name in request.headers:
                return JSONResponse(
                    status_code=400,
                    content={"error": "无效的请求头"}
                )

        # 2. 检查URL路径
        if _scan_request_value(str(request.url)):
            return JSONResponse(
                status_code=400,
                content={"error": "请求包含不安全内容"}
            )

        # 3. 检查查询参数
        for key, value in request.query_params.items():
            if _scan_request_value(value):
                return JSONResponse(
                    status_code=400,
                    content={"error": f"查询参数包含不安全内容"}
                )

        # 4. 检查请求体 (仅对POST/PUT/PATCH)
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    body_str = body.decode("utf-8", errors="ignore")
                    # 基本的XSS和注入检测
                    if len(body_str) > 100000:  # 100KB限制
                        return JSONResponse(
                            status_code=413,
                            content={"error": "请求体过大"}
                        )
                    if _scan_request_value(body_str):
                        return JSONResponse(
                            status_code=400,
                            content={"error": "请求内容包含不安全内容"}
                        )
                except Exception:
                    pass

        # 5. 处理请求并添加安全响应头
        response = await call_next(request)

        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        return response

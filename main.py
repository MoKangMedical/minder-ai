"""
Minder AI 红娘 - AI婚恋匹配平台

FastAPI 主应用入口。

功能概览:
- 智能匹配: 基于多维度加权算法的精准匹配
- AI红娘: 智能对话、约会建议、深度分析
- 实时聊天: WebSocket实时消息
- 健康评估: 语音/面部/性格/价值观/生活方式分析
- 订阅服务: 多级会员体系

技术栈:
- FastAPI + SQLAlchemy async
- WebSocket 实时通信
- 多维加权匹配算法
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from minder.db import init_db
from minder.api.middleware.rate_limiter import RateLimiterMiddleware
from minder.api.middleware.security import SecurityMiddleware
from minder.api.routers import (
    auth_router, users_router, matching_router,
    messages_router, health_router, payments_router,
    reports_router, ai_advisor_router
)


# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理。

    启动时:
    - 初始化数据库表
    - 加载配置
    - 预热AI模型 (生产环境)

    关闭时:
    - 清理资源
    - 关闭数据库连接
    """
    # 启动
    print("🌹 Minder AI 红娘 正在启动...")
    await init_db()
    print("✅ 数据库初始化完成")
    print("🚀 服务已就绪")

    yield

    # 关闭
    print("👋 Minder AI 红娘 正在关闭...")


# ==================== 创建应用 ====================

app = FastAPI(
    title="Minder AI 红娘",
    description=(
        "AI驱动的智能婚恋匹配平台。\n\n"
        "核心功能:\n"
        "- 🔍 **智能匹配** - 基于声音、颜值、性格、价值观、健康、生活方式六维匹配\n"
        "- 🤖 **AI红娘** - 智能对话、约会建议、深度分析\n"
        "- 💬 **实时聊天** - WebSocket实时消息\n"
        "- 📊 **健康评估** - 多维度个人健康报告\n"
        "- 💎 **订阅服务** - 多级会员体系\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==================== 中间件 ====================

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://minder.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全中间件
app.add_middleware(SecurityMiddleware)

# 速率限制中间件
app.add_middleware(RateLimiterMiddleware)


# ==================== 全局异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "detail": str(exc) if app.debug else "请联系技术支持",
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404 处理"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "资源不存在",
            "detail": f"路径 {request.url.path} 未找到",
        }
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    """请求验证错误处理"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "请求参数错误",
            "detail": str(exc),
        }
    )


# ==================== 注册路由 ====================

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(ai_advisor_router, prefix="/api/v1")


# ==================== 根路由 ====================

@app.get("/privacy", response_class=HTMLResponse, tags=["系统"])
async def privacy_page():
    """隐私政策"""
    p = FRONTEND_DIR / "templates" / "privacy.html"
    if p.exists(): return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Not found</h1>")


@app.get("/terms", response_class=HTMLResponse, tags=["系统"])
async def terms_page():
    """服务条款"""
    p = FRONTEND_DIR / "templates" / "terms.html"
    if p.exists(): return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Not found</h1>")


@app.get("/demo", response_class=HTMLResponse, tags=["系统"])
async def demo_page():
    """AI匹配体验页"""
    p = FRONTEND_DIR / "templates" / "demo.html"
    if p.exists(): return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Demo not found</h1>")


@app.get("/monitor", response_class=HTMLResponse, tags=["系统"])
async def monitor_page():
    """系统监控"""
    p = FRONTEND_DIR / "templates" / "monitor.html"
    if p.exists(): return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Not found</h1>")


@app.get("/admin", response_class=HTMLResponse, tags=["系统"])
async def admin_page():
    """管理后台"""
    p = FRONTEND_DIR / "templates" / "admin.html"
    if p.exists(): return HTMLResponse(p.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Admin not found</h1>")


@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查端点。

    用于负载均衡器和监控系统检测服务状态。
    """
    return {
        "status": "healthy",
        "service": "Minder AI 红娘",
        "version": "1.0.0",
    }


# ==================== 静态文件 & 前端 ====================

FRONTEND_DIR = Path(__file__).parent / "frontend"
if (FRONTEND_DIR / "templates").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/", tags=["系统"], response_class=HTMLResponse)
async def root():
    """产品首页"""
    index_path = FRONTEND_DIR / "templates" / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Minder AI 红娘</h1><p>前端文件未找到，请访问 <a href='/docs'>/docs</a> 查看API文档</p>")


# ==================== 运行入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "minder.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

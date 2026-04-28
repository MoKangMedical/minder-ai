# 🎯 Minder AI红娘

```
    __  __ _          _           
   |  \/  (_)_ _ _ __| |_ ___ _ _ 
   | |\/| | | '_| '_ \  _/ _ \ '_|
   |_|  |_|_|_| | .__/\__\___/_|  
                 |_|  AI红娘 v1.0  
```

> **用AI让每个人找到对的人** —— 基于多维AI分析的新一代智能婚恋匹配平台

---

## ✨ 核心功能

| 功能 | 描述 |
|------|------|
| 🎙️ **声纹情感分析** | 通过语音特征分析性格倾向与情绪稳定性 |
| 😊 **微表情识别** | AI面部特征分析，识别真实性格与情绪状态 |
| 🧠 **性格深度画像** | 基于大五人格模型的多维度性格分析 |
| 💡 **三观匹配引擎** | 价值观、世界观、人生观深度匹配算法 |
| 💪 **健康生活方式** | 运动、饮食、作息习惯综合评估 |
| 💌 **AI红娘对话** | 智能红娘主动撮合，提供恋爱指导建议 |

## 🛠️ 技术栈

```
┌─────────────────────────────────────────────────────┐
│                    Minder AI红娘                      │
├─────────────────────────────────────────────────────┤
│  FastAPI          │  高性能异步Web框架                  │
│  SQLAlchemy       │  ORM数据库管理 (SQLite/PostgreSQL)  │
│  WebSocket        │  实时消息通信                       │
│  6大AI引擎        │  声纹/表情/性格/三观/健康/生活方式     │
│  JWT              │  安全认证                           │
│  Redis            │  缓存与消息队列                     │
│  Docker           │  容器化部署                         │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- pip 或 poetry

### 安装与运行

```bash
# 1. 克隆项目
git clone https://github.com/minder-ai/minder.git
cd minder

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置你的API密钥

# 4. 初始化数据库
python scripts/init_db.py

# 5. 导入测试数据（可选）
python scripts/seed_data.py

# 6. 启动服务
uvicorn minder.main:app --reload --host 0.0.0.0 --port 8000

# 7. 打开浏览器
open http://localhost:8000/docs
```

### Docker 快速启动

```bash
docker-compose up -d
```

## 📡 API 概览

Minder 提供 **37个RESTful API端点**，按模块分组：

### 🔐 认证模块 (4个端点)
```
POST   /api/v1/auth/register      # 用户注册
POST   /api/v1/auth/login          # 用户登录
POST   /api/v1/auth/refresh        # 刷新令牌
POST   /api/v1/auth/logout         # 用户登出
```

### 👤 用户模块 (8个端点)
```
GET    /api/v1/users/me            # 获取当前用户信息
PUT    /api/v1/users/me            # 更新个人信息
POST   /api/v1/users/me/avatar     # 上传头像
GET    /api/v1/users/{id}          # 获取用户公开信息
GET    /api/v1/users/{id}/profile  # 获取用户详细资料
PUT    /api/v1/users/me/preferences # 更新择偶偏好
GET    /api/v1/users/me/stats      # 获取个人统计
DELETE /api/v1/users/me            # 注销账号
```

### 💘 匹配模块 (6个端点)
```
GET    /api/v1/matching/daily      # 每日推荐匹配
POST   /api/v1/matching/swipe      # 左滑/右滑
GET    /api/v1/matching/matches    # 获取匹配列表
GET    /api/v1/matching/{id}       # 获取匹配详情
POST   /api/v1/matching/ai-score   # AI匹配评分
DELETE /api/v1/matching/{id}       # 取消匹配
```

### 💬 消息模块 (6个端点)
```
GET    /api/v1/messages/conversations    # 获取会话列表
GET    /api/v1/messages/{conversation_id} # 获取聊天记录
POST   /api/v1/messages/send             # 发送消息
WS     /api/v1/messages/ws               # WebSocket实时消息
DELETE /api/v1/messages/{id}             # 删除消息
POST   /api/v1/messages/{id}/read        # 标记已读
```

### 🏥 健康模块 (4个端点)
```
GET    /api/v1/health/           # 健康检查
GET    /api/v1/health/ready      # 就绪检查
GET    /api/v1/health/live       # 存活检查
GET    /api/v1/health/metrics    # 系统指标
```

### 💰 支付模块 (4个端点)
```
POST   /api/v1/payment/create    # 创建支付订单
POST   /api/v1/payment/callback  # 支付回调
GET    /api/v1/payment/history   # 支付历史
GET    /api/v1/payment/plans     # 获取订阅计划
```

### 🚨 举报模块 (3个端点)
```
POST   /api/v1/report/           # 提交举报
GET    /api/v1/report/my         # 我的举报记录
GET    /api/v1/report/{id}       # 举报详情
```

### 🤖 AI红娘模块 (5个端点)
```
POST   /api/v1/ai/chat           # 与AI红娘对话
GET    /api/v1/ai/advice         # 获取恋爱建议
POST   /api/v1/ai/analyze        # AI分析匹配度
GET    /api/v1/ai/ice-breakers   # 获取破冰话题
GET    /api/v1/ai/date-plan      # 生成约会计划
```

### ⚙️ 系统模块 (3个端点)
```
GET    /api/v1/system/config     # 获取系统配置
GET    /api/v1/system/version    # 获取版本信息
POST   /api/v1/system/feedback   # 提交反馈
```

## 🏗️ 系统架构

```
                        ┌──────────────────┐
                        │   用户端 (Web/App) │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │   Nginx 反向代理   │
                        │   (SSL/TLS)       │
                        └────────┬─────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
            ┌───────▼──────┐ ┌──▼────────┐ ┌▼──────────┐
            │  FastAPI 应用  │ │ WebSocket │ │  AI 管道   │
            │  (REST API)   │ │   服务     │ │  引擎集群  │
            └───────┬──────┘ └──┬────────┘ └┬──────────┘
                    │            │            │
            ┌───────▼────────────▼────────────▼──────────┐
            │              服务层 (Service Layer)          │
            │  认证 │ 用户 │ 匹配 │ 消息 │ 支付 │ AI红娘   │
            └───────────────────┬─────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
    ┌───────▼───────┐   ┌──────▼──────┐   ┌───────▼───────┐
    │    SQLite/     │   │    Redis    │   │   文件存储     │
    │   PostgreSQL   │   │   缓存      │   │  (头像/语音)   │
    └───────────────┘   └─────────────┘   └───────────────┘

    AI Pipeline:
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ 声纹分析 │──▶│ 表情识别 │──▶│ 性格分析 │──▶│ 三观匹配 │
    └─────────┘   └─────────┘   └─────────┘   └─────────┘
                                                    │
    ┌─────────┐   ┌─────────┐                      │
    │ 生活方式 │◀──│ 健康评估 │◀─────────────────────┘
    └─────────┘   └─────────┘
```

## 🚢 部署指南

### Docker 部署（推荐）

```bash
# 构建镜像
docker build -t minder:latest .

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

### 手动部署

```bash
# 安装生产依赖
pip install gunicorn

# 使用 Gunicorn 启动
gunicorn minder.main:app \
  --config deploy/gunicorn.conf.py \
  --bind 0.0.0.0:8000
```

### 环境变量

```bash
# 复制示例配置
cp .env.example .env

# 必需配置项
DATABASE_URL=sqlite:///./minder.db
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379/0
AI_API_KEY=your-ai-api-key
```

## 🤝 参与贡献

我们欢迎所有形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

### 开发规范

- 代码风格：使用 Black 格式化，Ruff 检查
- 测试：确保所有测试通过 (`pytest tests/`)
- 文档：更新相关文档
- 提交：遵循 Conventional Commits 规范

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

```
MIT License

Copyright (c) 2024-2025 Minder AI红娘团队

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">

**用AI让每个人找到对的人** ❤️

[文档](docs/) · [API](docs/API.md) · [架构](docs/ARCHITECTURE.md) · [商业计划](docs/BUSINESS_PLAN.md)

</div>

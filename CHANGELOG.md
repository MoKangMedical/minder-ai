# Changelog

## v1.0.0 (2026-04-28)

### 新增
- FastAPI后端 (38路由, 30个API端点)
- 5个AI引擎: 语音分析/面部分析/健康评估/数字红娘/安全检测
- 6维匹配算法 (语音20%/面部15%/性格25%/价值观20%/健康10%/生活方式10%)
- WebSocket实时聊天
- JWT认证系统 (注册/登录/Token刷新)
- 限流中间件 (免费100次/分, VIP 500次/分)
- 安全中间件 (XSS/SQL注入/路径遍历防护)
- 暗色主题Landing Page (粒子动画/雷达图/定价/FAQ)
- 产品展示区 (手机模拟框+功能亮点)
- 信任徽章栏 (加密/全天候/GDPR/实名认证)
- AI匹配体验页 (/demo - 交互式匹配模拟)
- 管理后台 (/admin - 用户/匹配/收入仪表盘)
- 系统监控面板 (/monitor - API状态/性能指标)
- 隐私政策页 (/privacy)
- 服务条款页 (/terms)
- 投资人Pitch Deck (12页HTML演示)
- 微信小程序MVP (45文件, 6页面)
- 完整文档: README/API文档/架构文档/商业计划
- Docker + docker-compose + Nginx + CI/CD
- 30个测试用户种子数据
- 单元测试 + API集成测试
- Word整合方案文档

### 技术栈
- Python 3.12 + FastAPI + SQLAlchemy 2.0 async
- SQLite (开发) / PostgreSQL (生产)
- WebSocket实时通信
- numpy数值计算
- Pydantic数据验证
- JWT认证

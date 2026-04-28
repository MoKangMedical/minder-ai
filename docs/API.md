# 📡 Minder AI红娘 API 文档

> API版本: v1 | 基础路径: `/api/v1` | 认证方式: Bearer Token (JWT)

---

## 目录

- [认证模块](#认证模块)
- [用户模块](#用户模块)
- [匹配模块](#匹配模块)
- [消息模块](#消息模块)
- [健康模块](#健康模块)
- [支付模块](#支付模块)
- [举报模块](#举报模块)
- [AI红娘模块](#ai红娘模块)
- [系统模块](#系统模块)

---

## 认证模块

### 1. 用户注册

**POST** `/api/v1/auth/register`

**描述**: 注册新用户账号

**请求体**:
```json
{
  "username": "xiaoming",
  "email": "xiaoming@example.com",
  "password": "SecurePass123!",
  "phone": "13800138000",
  "gender": "male",
  "birth_date": "1995-06-15",
  "city": "北京"
}
```

**响应 (201)**:
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user_id": 1,
    "username": "xiaoming",
    "email": "xiaoming@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**错误响应 (400)**:
```json
{
  "code": 400,
  "message": "该邮箱已被注册",
  "data": null
}
```

---

### 2. 用户登录

**POST** `/api/v1/auth/login`

**描述**: 使用邮箱/手机和密码登录

**请求体**:
```json
{
  "email": "xiaoming@example.com",
  "password": "SecurePass123!"
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user_id": 1,
    "username": "xiaoming",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

### 3. 刷新令牌

**POST** `/api/v1/auth/refresh`

**描述**: 使用刷新令牌获取新的访问令牌

**请求头**:
```
Authorization: Bearer {refresh_token}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

### 4. 用户登出

**POST** `/api/v1/auth/logout`

**描述**: 注销当前会话

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

---

## 用户模块

### 5. 获取当前用户信息

**GET** `/api/v1/users/me`

**描述**: 获取当前登录用户的基本信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "xiaoming",
    "email": "xiaoming@example.com",
    "phone": "138****8000",
    "gender": "male",
    "birth_date": "1995-06-15",
    "age": 29,
    "city": "北京",
    "avatar_url": "https://cdn.minder.ai/avatars/1.jpg",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### 6. 更新个人信息

**PUT** `/api/v1/users/me`

**描述**: 更新当前用户的个人资料

**请求体**:
```json
{
  "nickname": "小明",
  "city": "上海",
  "bio": "热爱生活，喜欢旅行和摄影",
  "occupation": "软件工程师",
  "education": "本科",
  "height": 175,
  "income_range": "20-30万",
  "marital_status": "single",
  "hobbies": ["旅行", "摄影", "健身", "阅读"]
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "个人信息更新成功",
  "data": {
    "id": 1,
    "nickname": "小明",
    "city": "上海",
    "bio": "热爱生活，喜欢旅行和摄影",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

---

### 7. 上传头像

**POST** `/api/v1/users/me/avatar`

**描述**: 上传或更新用户头像

**请求**: `multipart/form-data`

| 字段 | 类型 | 描述 |
|------|------|------|
| avatar | file | 头像图片 (jpg/png, 最大5MB) |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "头像上传成功",
  "data": {
    "avatar_url": "https://cdn.minder.ai/avatars/1_v2.jpg"
  }
}
```

---

### 8. 获取用户公开信息

**GET** `/api/v1/users/{user_id}`

**描述**: 获取其他用户的公开资料

**路径参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| user_id | int | 用户ID |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "nickname": "小红",
    "gender": "female",
    "age": 27,
    "city": "北京",
    "avatar_url": "https://cdn.minder.ai/avatars/2.jpg",
    "bio": "喜欢读书和音乐",
    "education": "硕士",
    "occupation": "产品经理"
  }
}
```

---

### 9. 获取用户详细资料

**GET** `/api/v1/users/{user_id}/profile`

**描述**: 获取用户的详细资料（需已匹配）

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "nickname": "小红",
    "age": 27,
    "city": "北京",
    "height": 165,
    "weight": 52,
    "education": "硕士",
    "school": "北京大学",
    "occupation": "产品经理",
    "income_range": "20-30万",
    "marital_status": "single",
    "hobbies": ["读书", "音乐", "瑜伽", "烹饪"],
    "personality_tags": ["温柔", "独立", "上进"],
    "looking_for": {
      "age_range": [25, 35],
      "city": ["北京", "上海"],
      "education": "本科以上"
    }
  }
}
```

---

### 10. 更新择偶偏好

**PUT** `/api/v1/users/me/preferences`

**描述**: 设置择偶偏好条件

**请求体**:
```json
{
  "age_min": 22,
  "age_max": 30,
  "gender": "female",
  "city_preference": ["北京", "上海", "杭州"],
  "education_min": "本科",
  "height_min": 160,
  "height_max": 175,
  "income_min": "10-20万",
  "deal_breakers": ["吸烟", "离异"],
  "importance_tags": ["三观一致", "性格互补", "有共同爱好"]
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "择偶偏好更新成功",
  "data": {
    "age_min": 22,
    "age_max": 30,
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

---

### 11. 获取个人统计

**GET** `/api/v1/users/me/stats`

**描述**: 获取个人匹配和互动统计数据

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "profile_views": 156,
    "likes_received": 23,
    "likes_sent": 15,
    "matches": 8,
    "conversations": 5,
    "ai_score": 87.5,
    "profile_completeness": 85,
    "active_days": 30
  }
}
```

---

### 12. 注销账号

**DELETE** `/api/v1/users/me`

**描述**: 注销当前用户账号（需二次确认）

**请求体**:
```json
{
  "password": "SecurePass123!",
  "reason": "找到了另一半",
  "confirm": true
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "账号已注销，感谢使用Minder",
  "data": null
}
```

---

## 匹配模块

### 13. 每日推荐匹配

**GET** `/api/v1/matching/daily`

**描述**: 获取每日推荐的匹配对象

**查询参数**:
| 参数 | 类型 | 默认 | 描述 |
|------|------|------|------|
| limit | int | 10 | 推荐数量 |
| offset | int | 0 | 偏移量 |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "recommendations": [
      {
        "user_id": 2,
        "nickname": "小红",
        "age": 27,
        "city": "北京",
        "avatar_url": "https://cdn.minder.ai/avatars/2.jpg",
        "bio": "喜欢读书和音乐",
        "ai_match_score": 92.5,
        "compatibility": {
          "personality": 88,
          "values": 95,
          "lifestyle": 90,
          "overall": 92.5
        },
        "common_tags": ["旅行", "阅读"]
      }
    ],
    "total": 25,
    "remaining_today": 15
  }
}
```

---

### 14. 左滑/右滑

**POST** `/api/v1/matching/swipe`

**描述**: 对推荐用户进行喜欢或跳过操作

**请求体**:
```json
{
  "target_user_id": 2,
  "action": "like",
  "super_like": false
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| target_user_id | int | 目标用户ID |
| action | string | `like` 或 `pass` |
| super_like | bool | 是否超级喜欢（每日限3次） |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "匹配成功！",
  "data": {
    "is_match": true,
    "match_id": 42,
    "matched_user": {
      "id": 2,
      "nickname": "小红",
      "avatar_url": "https://cdn.minder.ai/avatars/2.jpg"
    },
    "can_chat": true
  }
}
```

---

### 15. 获取匹配列表

**GET** `/api/v1/matching/matches`

**描述**: 获取所有匹配成功的用户列表

**查询参数**:
| 参数 | 类型 | 默认 | 描述 |
|------|------|------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量 |
| sort_by | string | "recent" | 排序方式: recent/score/active |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "matches": [
      {
        "match_id": 42,
        "user": {
          "id": 2,
          "nickname": "小红",
          "age": 27,
          "city": "北京",
          "avatar_url": "https://cdn.minder.ai/avatars/2.jpg"
        },
        "matched_at": "2024-01-15T14:30:00Z",
        "last_message": "你好，很高兴认识你！",
        "ai_score": 92.5,
        "is_new": true
      }
    ],
    "total": 8,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 16. 获取匹配详情

**GET** `/api/v1/matching/{match_id}`

**描述**: 获取特定匹配的详细信息

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "match_id": 42,
    "user": {
      "id": 2,
      "nickname": "小红",
      "age": 27,
      "city": "北京",
      "avatar_url": "https://cdn.minder.ai/avatars/2.jpg"
    },
    "matched_at": "2024-01-15T14:30:00Z",
    "ai_score": 92.5,
    "compatibility_report": {
      "personality_match": "性格互补，内向与外向形成良好平衡",
      "values_match": "三观高度一致，对家庭和事业的看法相近",
      "lifestyle_match": "生活习惯相似，作息时间匹配",
      "suggestions": ["可以从旅行话题开始", "两人都喜欢美食"]
    }
  }
}
```

---

### 17. AI匹配评分

**POST** `/api/v1/matching/ai-score`

**描述**: 计算与指定用户的AI匹配评分

**请求体**:
```json
{
  "target_user_id": 2,
  "include_report": true
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "overall_score": 92.5,
    "dimensions": {
      "personality": {
        "score": 88,
        "detail": "性格互补度高，沟通风格匹配"
      },
      "values": {
        "score": 95,
        "detail": "三观高度一致，人生目标相近"
      },
      "lifestyle": {
        "score": 90,
        "detail": "生活习惯相似，兴趣爱好重叠度70%"
      },
      "communication": {
        "score": 85,
        "detail": "沟通风格互补，表达方式匹配"
      },
      "emotion": {
        "score": 92,
        "detail": "情绪稳定性匹配，共情能力强"
      }
    },
    "report": "基于AI多维度分析，你们的匹配度非常高..."
  }
}
```

---

### 18. 取消匹配

**DELETE** `/api/v1/matching/{match_id}`

**描述**: 取消与某用户的匹配关系

**响应 (200)**:
```json
{
  "code": 200,
  "message": "匹配已取消",
  "data": null
}
```

---

## 消息模块

### 19. 获取会话列表

**GET** `/api/v1/messages/conversations`

**描述**: 获取所有会话列表

**查询参数**:
| 参数 | 类型 | 默认 | 描述 |
|------|------|------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量 |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "conversations": [
      {
        "conversation_id": "conv_42",
        "user": {
          "id": 2,
          "nickname": "小红",
          "avatar_url": "https://cdn.minder.ai/avatars/2.jpg",
          "is_online": true
        },
        "last_message": {
          "content": "周末有空一起喝咖啡吗？",
          "timestamp": "2024-01-15T16:45:00Z",
          "sender_id": 2
        },
        "unread_count": 2
      }
    ],
    "total": 5
  }
}
```

---

### 20. 获取聊天记录

**GET** `/api/v1/messages/{conversation_id}`

**描述**: 获取指定会话的聊天记录

**查询参数**:
| 参数 | 类型 | 默认 | 描述 |
|------|------|------|------|
| before | string | null | 分页游标（消息ID） |
| limit | int | 50 | 消息数量 |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "messages": [
      {
        "id": "msg_001",
        "sender_id": 1,
        "content": "你好，很高兴认识你！",
        "type": "text",
        "timestamp": "2024-01-15T14:30:00Z",
        "is_read": true
      },
      {
        "id": "msg_002",
        "sender_id": 2,
        "content": "你好呀，我也很高兴！",
        "type": "text",
        "timestamp": "2024-01-15T14:31:00Z",
        "is_read": true
      }
    ],
    "has_more": true,
    "cursor": "msg_002"
  }
}
```

---

### 21. 发送消息

**POST** `/api/v1/messages/send`

**描述**: 发送消息给匹配用户

**请求体**:
```json
{
  "conversation_id": "conv_42",
  "content": "周末有空一起喝咖啡吗？",
  "type": "text"
}
```

| type 可选值 | 描述 |
|------------|------|
| text | 文本消息 |
| image | 图片消息 |
| voice | 语音消息 |
| ice_breaker | AI破冰话题 |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "消息发送成功",
  "data": {
    "id": "msg_003",
    "conversation_id": "conv_42",
    "content": "周末有空一起喝咖啡吗？",
    "timestamp": "2024-01-15T16:45:00Z",
    "status": "sent"
  }
}
```

---

### 22. WebSocket实时消息

**WS** `/api/v1/messages/ws?token={access_token}`

**描述**: 建立WebSocket连接用于实时消息

**连接参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| token | string | JWT访问令牌 |

**客户端发送**:
```json
{
  "type": "message",
  "conversation_id": "conv_42",
  "content": "你好！",
  "msg_type": "text"
}
```

**服务端推送**:
```json
{
  "type": "new_message",
  "data": {
    "id": "msg_004",
    "sender_id": 2,
    "conversation_id": "conv_42",
    "content": "你好呀！",
    "timestamp": "2024-01-15T16:46:00Z"
  }
}
```

**事件类型**:
| type | 描述 |
|------|------|
| message | 新消息 |
| typing | 对方正在输入 |
| read | 消息已读 |
| online | 用户上线 |
| offline | 用户下线 |
| match | 新匹配通知 |

---

### 23. 删除消息

**DELETE** `/api/v1/messages/{message_id}`

**描述**: 删除自己发送的消息（2分钟内）

**响应 (200)**:
```json
{
  "code": 200,
  "message": "消息已删除",
  "data": null
}
```

---

### 24. 标记已读

**POST** `/api/v1/messages/{conversation_id}/read`

**描述**: 标记会话中所有消息为已读

**响应 (200)**:
```json
{
  "code": 200,
  "message": "已标记为已读",
  "data": {
    "conversation_id": "conv_42",
    "read_count": 5,
    "read_at": "2024-01-15T17:00:00Z"
  }
}
```

---

## 健康模块

### 25. 健康检查

**GET** `/api/v1/health/`

**描述**: 系统健康状态检查

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": "3d 12h 45m",
    "timestamp": "2024-01-15T12:00:00Z"
  }
}
```

---

### 26. 就绪检查

**GET** `/api/v1/health/ready`

**描述**: 检查服务是否就绪（用于Kubernetes readinessProbe）

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ready": true,
    "checks": {
      "database": "ok",
      "redis": "ok",
      "ai_engine": "ok"
    }
  }
}
```

---

### 27. 存活检查

**GET** `/api/v1/health/live`

**描述**: 检查服务是否存活（用于Kubernetes livenessProbe）

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "alive": true
  }
}
```

---

### 28. 系统指标

**GET** `/api/v1/health/metrics`

**描述**: 获取系统运行指标

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "requests_per_minute": 150,
    "active_connections": 45,
    "memory_usage_mb": 512,
    "cpu_usage_percent": 35.5,
    "database_pool_size": 10,
    "database_pool_available": 7,
    "redis_connected": true
  }
}
```

---

## 支付模块

### 29. 创建支付订单

**POST** `/api/v1/payment/create`

**描述**: 创建订阅支付订单

**请求体**:
```json
{
  "plan_id": "premium_monthly",
  "payment_method": "alipay",
  "coupon_code": "FIRST50"
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "订单创建成功",
  "data": {
    "order_id": "ORD_20240115_001",
    "amount": 99.00,
    "discount": 49.50,
    "final_amount": 49.50,
    "payment_url": "https://pay.minder.ai/order/ORD_20240115_001",
    "expire_at": "2024-01-15T12:30:00Z"
  }
}
```

---

### 30. 支付回调

**POST** `/api/v1/payment/callback`

**描述**: 支付平台回调通知（内部使用）

**请求体**:
```json
{
  "order_id": "ORD_20240115_001",
  "status": "success",
  "transaction_id": "TXN_123456789",
  "amount": 49.50,
  "sign": "a1b2c3d4e5f6..."
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "ok",
  "data": null
}
```

---

### 31. 支付历史

**GET** `/api/v1/payment/history`

**描述**: 获取用户的支付历史记录

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "orders": [
      {
        "order_id": "ORD_20240115_001",
        "plan_name": "高级会员（月卡）",
        "amount": 49.50,
        "status": "paid",
        "paid_at": "2024-01-15T12:15:00Z",
        "expires_at": "2024-02-15T12:15:00Z"
      }
    ],
    "total_spent": 49.50
  }
}
```

---

### 32. 获取订阅计划

**GET** `/api/v1/payment/plans`

**描述**: 获取所有可用的订阅计划

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "plans": [
      {
        "id": "free",
        "name": "免费版",
        "price": 0,
        "period": null,
        "features": ["每日5个推荐", "基础匹配", "3次聊天/天"],
        "is_current": true
      },
      {
        "id": "premium_monthly",
        "name": "高级会员（月卡）",
        "price": 99,
        "discount_price": 49.5,
        "period": "monthly",
        "features": ["无限推荐", "AI深度匹配", "无限聊天", "查看谁喜欢你", "优先客服"],
        "is_popular": true
      },
      {
        "id": "premium_yearly",
        "name": "高级会员（年卡）",
        "price": 999,
        "discount_price": 599,
        "period": "yearly",
        "features": ["所有月卡功能", "专属红娘服务", "线下活动优先", "VIP标识"],
        "savings": "省40%"
      }
    ]
  }
}
```

---

## 举报模块

### 33. 提交举报

**POST** `/api/v1/report/`

**描述**: 举报用户或内容

**请求体**:
```json
{
  "target_user_id": 15,
  "reason": "fake_profile",
  "description": "该用户使用虚假照片，与实际不符",
  "evidence_urls": ["https://cdn.minder.ai/evidence/001.jpg"],
  "block_user": true
}
```

| reason 可选值 | 描述 |
|--------------|------|
| fake_profile | 虚假资料 |
| harassment | 骚扰行为 |
| spam | 垃圾信息 |
| inappropriate | 不当内容 |
| scam | 欺诈行为 |
| other | 其他 |

**响应 (201)**:
```json
{
  "code": 200,
  "message": "举报已提交，我们将在24小时内处理",
  "data": {
    "report_id": "RPT_001",
    "status": "pending",
    "estimated_review": "24小时内"
  }
}
```

---

### 34. 我的举报记录

**GET** `/api/v1/report/my`

**描述**: 获取当前用户的举报记录

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reports": [
      {
        "report_id": "RPT_001",
        "target_user": {
          "id": 15,
          "nickname": "可疑用户"
        },
        "reason": "fake_profile",
        "status": "resolved",
        "result": "已封禁该账号",
        "submitted_at": "2024-01-10T10:00:00Z",
        "resolved_at": "2024-01-11T08:00:00Z"
      }
    ],
    "total": 1
  }
}
```

---

### 35. 举报详情

**GET** `/api/v1/report/{report_id}`

**描述**: 获取举报处理详情

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "report_id": "RPT_001",
    "target_user_id": 15,
    "reason": "fake_profile",
    "description": "该用户使用虚假照片",
    "status": "resolved",
    "result": "已封禁该账号",
    "submitted_at": "2024-01-10T10:00:00Z",
    "resolved_at": "2024-01-11T08:00:00Z",
    "resolution_notes": "经核实，该账号确实使用虚假照片，已永久封禁"
  }
}
```

---

## AI红娘模块

### 36. 与AI红娘对话

**POST** `/api/v1/ai/chat`

**描述**: 与AI红娘进行智能对话

**请求体**:
```json
{
  "message": "我应该怎么和匹配的女生开始聊天？",
  "context": {
    "match_id": 42,
    "conversation_history": true
  }
}
```

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reply": "根据小红的资料，她喜欢读书和音乐，建议你可以从这两个话题开始。比如：'我看到你也喜欢读书，最近在读什么好书吗？'这样的开场白既自然又能找到共同话题。",
    "suggestions": [
      "可以聊聊最近读的书",
      "问问她喜欢的音乐类型",
      "分享一个有趣的旅行经历"
    ],
    "ice_breakers": [
      "如果可以拥有一种超能力，你会选什么？",
      "最近有什么让你开心的小事吗？"
    ]
  }
}
```

---

### 37. 获取恋爱建议

**GET** `/api/v1/ai/advice`

**描述**: 获取个性化的恋爱建议

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| topic | string | 主题: dating/chatting/relationship/profile |
| match_id | int | 可选，针对特定匹配的建议 |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "advice": {
      "topic": "dating",
      "tips": [
        {
          "title": "第一次约会建议",
          "content": "选择轻松的咖啡厅或公园，避免过于正式的场合",
          "priority": "high"
        },
        {
          "title": "约会前准备",
          "content": "提前了解对方的兴趣，准备几个聊天话题",
          "priority": "medium"
        }
      ],
      "personalized": true
    }
  }
}
```

---

### 38. AI分析匹配度

**POST** `/api/v1/ai/analyze`

**描述**: AI深度分析两个用户的匹配度

**请求体**:
```json
{
  "target_user_id": 2,
  "analysis_type": "full"
}
```

| analysis_type | 描述 |
|--------------|------|
| quick | 快速分析（5秒） |
| standard | 标准分析（15秒） |
| full | 完整分析（30秒，含6大维度） |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "analysis_id": "ANA_001",
    "overall_score": 92.5,
    "dimensions": {
      "voice": {"score": 85, "detail": "声纹特征显示情绪稳定，表达温和"},
      "face": {"score": 88, "detail": "微表情分析显示真诚友善"},
      "personality": {"score": 90, "detail": "性格互补度高"},
      "values": {"score": 95, "detail": "三观高度一致"},
      "health": {"score": 88, "detail": "健康生活方式匹配"},
      "lifestyle": {"score": 92, "detail": "生活习惯高度契合"}
    },
    "summary": "综合分析显示，你们的匹配度非常高（92.5分）...",
    "generated_at": "2024-01-15T12:00:00Z"
  }
}
```

---

### 39. 获取破冰话题

**GET** `/api/v1/ai/ice-breakers`

**描述**: 获取AI生成的破冰话题

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| match_id | int | 匹配ID |
| count | int | 话题数量（默认5） |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ice_breakers": [
      {
        "id": 1,
        "topic": "如果你可以瞬间传送到世界上任何一个地方，你会去哪里？",
        "category": "travel",
        "follow_up": "那里有什么特别吸引你的地方吗？"
      },
      {
        "id": 2,
        "topic": "你最近在追什么剧或者看什么书吗？",
        "category": "entertainment",
        "follow_up": "我也很喜欢这个类型！你觉得怎么样？"
      },
      {
        "id": 3,
        "topic": "如果让你开一家小店，你会开什么店？",
        "category": "dreams",
        "follow_up": "这个想法太棒了，是什么启发了你？"
      }
    ]
  }
}
```

---

### 40. 生成约会计划

**GET** `/api/v1/ai/date-plan`

**描述**: AI生成约会计划建议

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| match_id | int | 匹配ID |
| budget | string | 预算: low/medium/high |
| style | string | 风格: casual/romantic/adventure |

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "date_plan": {
      "title": "文艺咖啡厅约会",
      "duration": "3小时",
      "budget": "约200元",
      "schedule": [
        {
          "time": "14:00",
          "activity": "在朝阳区的独立咖啡厅见面",
          "location": "北京朝阳区三里屯",
          "tip": "提前10分钟到，选个靠窗的位置"
        },
        {
          "time": "15:00",
          "activity": "一起逛附近的书店",
          "location": "三里屯PageOne书店",
          "tip": "可以分享各自喜欢的书"
        },
        {
          "time": "16:30",
          "activity": "在公园散步聊天",
          "location": "朝阳公园",
          "tip": "夕阳西下，气氛很好"
        }
      ],
      "conversation_topics": [
        "分享最近读的书",
        "聊聊旅行经历",
        "讨论未来的计划"
      ]
    }
  }
}
```

---

## 系统模块

### 41. 获取系统配置

**GET** `/api/v1/system/config`

**描述**: 获取客户端需要的系统配置

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "max_avatar_size_mb": 5,
    "allowed_image_types": ["jpg", "jpeg", "png", "webp"],
    "max_bio_length": 500,
    "max_photos": 9,
    "daily_swipe_limit": 50,
    "super_like_daily_limit": 3,
    "message_rate_limit": 30,
    "maintenance_mode": false,
    "min_app_version": "1.0.0"
  }
}
```

---

### 42. 获取版本信息

**GET** `/api/v1/system/version`

**描述**: 获取系统版本信息

**响应 (200)**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "version": "1.0.0",
    "build": "20240115",
    "api_version": "v1",
    "release_notes": "首次发布，包含核心匹配功能"
  }
}
```

---

### 43. 提交反馈

**POST** `/api/v1/system/feedback`

**描述**: 提交用户反馈

**请求体**:
```json
{
  "type": "suggestion",
  "content": "希望增加语音聊天功能",
  "contact": "xiaoming@example.com",
  "attachments": []
}
```

| type 可选值 | 描述 |
|------------|------|
| bug | Bug反馈 |
| suggestion | 功能建议 |
| complaint | 投诉 |
| praise | 表扬 |

**响应 (201)**:
```json
{
  "code": 200,
  "message": "感谢您的反馈！我们会认真考虑",
  "data": {
    "feedback_id": "FB_001",
    "status": "received"
  }
}
```

---

## 错误码说明

| 错误码 | 描述 | HTTP状态码 |
|--------|------|-----------|
| 200 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 422 | 数据验证失败 | 422 |
| 429 | 请求过于频繁 | 429 |
| 500 | 服务器内部错误 | 500 |

**通用错误响应格式**:
```json
{
  "code": 400,
  "message": "错误描述信息",
  "data": null,
  "detail": "详细的错误信息（仅开发环境）"
}
```

---

## 请求限制

| 限制类型 | 免费用户 | 高级会员 |
|---------|---------|---------|
| 每日推荐 | 5次 | 无限 |
| 每日滑动 | 50次 | 无限 |
| 超级喜欢 | 3次/天 | 10次/天 |
| AI对话 | 3次/天 | 无限 |
| API请求 | 100次/分钟 | 300次/分钟 |

---

## 认证说明

所有需要认证的接口需要在请求头中携带JWT令牌：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

令牌有效期：1小时
刷新令牌有效期：30天

---

## 更新日志

### v1.0.0 (2024-01-15)
- 首次发布
- 37个API端点
- 6大AI匹配引擎
- 实时WebSocket消息

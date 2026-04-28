"""
Minder AI红娘 - API端点测试
使用 httpx 进行异步API测试
"""

import pytest
import httpx
from typing import AsyncGenerator


# ============================================================
# 测试配置
# ============================================================

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 测试用户数据
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123456!",
    "phone": "13900000000",
    "gender": "male",
    "birth_date": "1995-01-01",
    "city": "北京",
}


# ============================================================
# 辅助函数
# ============================================================

async def get_auth_headers(client: httpx.AsyncClient) -> dict:
    """获取认证头"""
    # 先注册
    await client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)

    # 再登录
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    data = response.json()
    token = data.get("data", {}).get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 认证模块测试
# ============================================================

class TestAuth:
    """认证模块测试"""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """测试用户注册成功"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                f"{API_PREFIX}/auth/register",
                json={
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "Test123456!",
                    "phone": "13900001111",
                    "gender": "female",
                    "birth_date": "1997-06-15",
                    "city": "上海",
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert data["code"] == 200
            assert "access_token" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """测试重复邮箱注册"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 第一次注册
            await client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)

            # 第二次注册相同邮箱
            response = await client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(self):
        """测试无效邮箱"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                f"{API_PREFIX}/auth/register",
                json={**TEST_USER, "email": "invalid-email"}
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password(self):
        """测试弱密码"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                f"{API_PREFIX}/auth/register",
                json={**TEST_USER, "password": "123"}
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self):
        """测试登录成功"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 先注册
            await client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)

            # 登录
            response = await client.post(
                f"{API_PREFIX}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data.get("data", {})
            assert "refresh_token" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        """测试错误密码"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 先注册
            await client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)

            # 用错误密码登录
            response = await client.post(
                f"{API_PREFIX}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        """测试不存在的用户"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                f"{API_PREFIX}/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "Test123456!"
                }
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self):
        """测试刷新令牌"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 注册并登录
            await client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)
            login_response = await client.post(
                f"{API_PREFIX}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            refresh_token = login_response.json()["data"]["refresh_token"]

            # 刷新令牌
            response = await client.post(
                f"{API_PREFIX}/auth/refresh",
                headers={"Authorization": f"Bearer {refresh_token}"}
            )
            assert response.status_code == 200
            assert "access_token" in response.json().get("data", {})

    @pytest.mark.asyncio
    async def test_logout(self):
        """测试登出"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/auth/logout",
                headers=headers
            )
            assert response.status_code == 200


# ============================================================
# 用户模块测试
# ============================================================

class TestUsers:
    """用户模块测试"""

    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """测试获取当前用户"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/users/me",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["email"] == TEST_USER["email"]

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self):
        """测试未认证获取用户"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/users/me")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile(self):
        """测试更新个人资料"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.put(
                f"{API_PREFIX}/users/me",
                headers=headers,
                json={
                    "nickname": "测试用户",
                    "bio": "这是一个测试用户",
                    "occupation": "测试工程师",
                    "education": "本科",
                    "height": 175,
                    "hobbies": ["测试", "编程"],
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_user_stats(self):
        """测试获取用户统计"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/users/me/stats",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "profile_views" in data.get("data", {})
            assert "matches" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_update_preferences(self):
        """测试更新择偶偏好"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.put(
                f"{API_PREFIX}/users/me/preferences",
                headers=headers,
                json={
                    "age_min": 22,
                    "age_max": 30,
                    "city_preference": ["北京", "上海"],
                    "education_min": "本科",
                }
            )
            assert response.status_code == 200


# ============================================================
# 匹配模块测试
# ============================================================

class TestMatching:
    """匹配模块测试"""

    @pytest.mark.asyncio
    async def test_get_daily_recommendations(self):
        """测试获取每日推荐"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/matching/daily",
                headers=headers,
                params={"limit": 10}
            )
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_swipe_like(self):
        """测试右滑（喜欢）"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/matching/swipe",
                headers=headers,
                json={
                    "target_user_id": 2,
                    "action": "like",
                    "super_like": False,
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_swipe_pass(self):
        """测试左滑（跳过）"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/matching/swipe",
                headers=headers,
                json={
                    "target_user_id": 3,
                    "action": "pass",
                    "super_like": False,
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_matches(self):
        """测试获取匹配列表"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/matching/matches",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "matches" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_ai_score(self):
        """测试AI匹配评分"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/matching/ai-score",
                headers=headers,
                json={
                    "target_user_id": 2,
                    "include_report": True,
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "overall_score" in data.get("data", {})


# ============================================================
# 消息模块测试
# ============================================================

class TestMessages:
    """消息模块测试"""

    @pytest.mark.asyncio
    async def test_get_conversations(self):
        """测试获取会话列表"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/messages/conversations",
                headers=headers
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message(self):
        """测试发送消息"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/messages/send",
                headers=headers,
                json={
                    "conversation_id": "conv_1",
                    "content": "你好！",
                    "type": "text",
                }
            )
            # 如果没有匹配，可能会返回404
            assert response.status_code in [200, 404]


# ============================================================
# 健康检查测试
# ============================================================

class TestHealth:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/health/")
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_readiness_check(self):
        """测试就绪检查"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["ready"] is True

    @pytest.mark.asyncio
    async def test_liveness_check(self):
        """测试存活检查"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["alive"] is True

    @pytest.mark.asyncio
    async def test_metrics(self):
        """测试系统指标"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/health/metrics")
            assert response.status_code == 200


# ============================================================
# 支付模块测试
# ============================================================

class TestPayment:
    """支付模块测试"""

    @pytest.mark.asyncio
    async def test_get_plans(self):
        """测试获取订阅计划"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/payment/plans",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            plans = data.get("data", {}).get("plans", [])
            assert len(plans) > 0
            assert any(p["id"] == "free" for p in plans)

    @pytest.mark.asyncio
    async def test_get_payment_history(self):
        """测试获取支付历史"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/payment/history",
                headers=headers
            )
            assert response.status_code == 200


# ============================================================
# AI红娘模块测试
# ============================================================

class TestAI:
    """AI红娘模块测试"""

    @pytest.mark.asyncio
    async def test_ai_chat(self):
        """测试AI对话"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/ai/chat",
                headers=headers,
                json={
                    "message": "我应该怎么开始聊天？",
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "reply" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_get_ice_breakers(self):
        """测试获取破冰话题"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/ai/ice-breakers",
                headers=headers,
                params={"count": 5}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_advice(self):
        """测试获取恋爱建议"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/ai/advice",
                headers=headers,
                params={"topic": "dating"}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_date_plan(self):
        """测试获取约会计划"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/ai/date-plan",
                headers=headers,
                params={
                    "match_id": 1,
                    "budget": "medium",
                    "style": "casual",
                }
            )
            assert response.status_code == 200


# ============================================================
# 系统模块测试
# ============================================================

class TestSystem:
    """系统模块测试"""

    @pytest.mark.asyncio
    async def test_get_config(self):
        """测试获取系统配置"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/system/config")
            assert response.status_code == 200
            data = response.json()
            assert "max_avatar_size_mb" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_get_version(self):
        """测试获取版本信息"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/system/version")
            assert response.status_code == 200
            data = response.json()
            assert "version" in data.get("data", {})

    @pytest.mark.asyncio
    async def test_submit_feedback(self):
        """测试提交反馈"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/system/feedback",
                headers=headers,
                json={
                    "type": "suggestion",
                    "content": "希望增加语音聊天功能",
                }
            )
            assert response.status_code == 201


# ============================================================
# 举报模块测试
# ============================================================

class TestReport:
    """举报模块测试"""

    @pytest.mark.asyncio
    async def test_submit_report(self):
        """测试提交举报"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.post(
                f"{API_PREFIX}/report/",
                headers=headers,
                json={
                    "target_user_id": 999,
                    "reason": "fake_profile",
                    "description": "使用虚假照片",
                }
            )
            assert response.status_code in [201, 404]

    @pytest.mark.asyncio
    async def test_get_my_reports(self):
        """测试获取我的举报"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            headers = await get_auth_headers(client)

            response = await client.get(
                f"{API_PREFIX}/report/my",
                headers=headers
            )
            assert response.status_code == 200


# ============================================================
# 性能测试
# ============================================================

class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_health_check_response_time(self):
        """测试健康检查响应时间"""
        import time

        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            start = time.time()
            response = await client.get(f"{API_PREFIX}/health/")
            elapsed = time.time() - start

            assert response.status_code == 200
            assert elapsed < 1.0  # 响应时间应小于1秒

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""
        import asyncio

        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            tasks = [
                client.get(f"{API_PREFIX}/health/")
                for _ in range(10)
            ]
            responses = await asyncio.gather(*tasks)

            for response in responses:
                assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

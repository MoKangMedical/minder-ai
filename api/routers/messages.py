"""
Minder AI 红娘 - 消息路由

处理会话列表、消息发送/接收、WebSocket实时聊天等功能。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Set

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from minder.db import get_db, User, Match, Message, MatchStatus
from minder.schemas import (
    ConversationSummary, MessageResponse, MessageCreate,
    UserPublicProfile, SuccessResponse
)
from minder.api.routers.auth import get_current_user

router = APIRouter(tags=["消息"])


# ==================== WebSocket 连接管理 ====================

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # {match_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int, user_id: int):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = {}
        self.active_connections[match_id][user_id] = websocket

    def disconnect(self, match_id: int, user_id: int):
        if match_id in self.active_connections:
            self.active_connections[match_id].pop(user_id, None)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]

    async def send_to_user(self, match_id: int, user_id: int, message: dict):
        if match_id in self.active_connections:
            ws = self.active_connections[match_id].get(user_id)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(match_id, user_id)

    async def broadcast_to_match(self, match_id: int, message: dict, exclude_user: int = None):
        if match_id in self.active_connections:
            for uid, ws in self.active_connections[match_id].items():
                if uid != exclude_user:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        self.disconnect(match_id, uid)


manager = ConnectionManager()


# ==================== REST 端点 ====================

def _user_to_public(user: User) -> UserPublicProfile:
    """转换用户为公开资料"""
    from minder.api.routers.users import _user_to_public as convert
    return convert(user)


@router.get("/conversations", response_model=List[ConversationSummary], summary="会话列表")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有会话列表。

    仅显示互相匹配的会话。
    按最后消息时间排序。
    """
    # 获取互相匹配的记录
    result = await db.execute(
        select(Match)
        .where(
            or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id),
            Match.is_mutual == True
        )
        .options(selectinload(Match.user_a), selectinload(Match.user_b))
    )
    matches = result.scalars().all()

    conversations = []
    for match in matches:
        partner = match.user_b if match.user_a_id == current_user.id else match.user_a

        # 获取最后一条消息
        msg_result = await db.execute(
            select(Message)
            .where(Message.match_id == match.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()

        # 获取未读消息数
        unread_result = await db.execute(
            select(func.count(Message.id))
            .where(
                Message.match_id == match.id,
                Message.sender_id != current_user.id,
                Message.is_read == False
            )
        )
        unread_count = unread_result.scalar() or 0

        last_message = None
        if last_msg:
            last_message = MessageResponse(
                id=last_msg.id,
                match_id=last_msg.match_id,
                sender_id=last_msg.sender_id,
                content=last_msg.content,
                message_type=last_msg.message_type,
                is_read=last_msg.is_read,
                created_at=last_msg.created_at,
            )

        conversations.append(ConversationSummary(
            match_id=match.id,
            partner=_user_to_public(partner),
            last_message=last_message,
            unread_count=unread_count,
        ))

    # 按最后消息时间排序
    conversations.sort(
        key=lambda c: c.last_message.created_at if c.last_message else datetime.min,
        reverse=True
    )

    return conversations


@router.get("/conversations/{match_id}/messages", response_model=List[MessageResponse], summary="获取消息")
async def get_messages(
    match_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定会话的消息列表。

    分页加载, 默认每页50条, 倒序返回 (最新消息在前)。
    """
    # 验证匹配关系
    result = await db.execute(
        select(Match).where(
            Match.id == match_id,
            or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id)
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="会话不存在")

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(Message.match_id == match_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    messages = result.scalars().all()

    # 标记消息为已读
    unread_ids = [
        m.id for m in messages
        if m.sender_id != current_user.id and not m.is_read
    ]
    if unread_ids:
        for msg in messages:
            if msg.id in unread_ids:
                msg.is_read = True
        await db.commit()

    return [
        MessageResponse(
            id=m.id,
            match_id=m.match_id,
            sender_id=m.sender_id,
            content=m.content,
            message_type=m.message_type,
            is_read=m.is_read,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/conversations/{match_id}/messages", response_model=MessageResponse, summary="发送消息")
async def send_message(
    match_id: int,
    msg: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    在指定会话中发送消息。

    仅互相匹配的用户可以发送消息。
    """
    # 验证匹配关系和互相匹配
    result = await db.execute(
        select(Match).where(
            Match.id == match_id,
            or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id),
            Match.is_mutual == True
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="会话不存在或未互相匹配")

    message = Message(
        match_id=match_id,
        sender_id=current_user.id,
        content=msg.content,
        message_type=msg.message_type,
        is_read=False,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    msg_response = MessageResponse(
        id=message.id,
        match_id=message.match_id,
        sender_id=message.sender_id,
        content=message.content,
        message_type=message.message_type,
        is_read=message.is_read,
        created_at=message.created_at,
    )

    # 通过WebSocket通知对方
    partner_id = match.user_b if match.user_a_id == current_user.id else match.user_a
    await manager.send_to_user(match_id, partner_id, {
        "type": "new_message",
        "message": msg_response.model_dump(mode="json"),
    })

    return msg_response


# ==================== WebSocket ====================

@router.websocket("/ws/chat/{match_id}")
async def websocket_chat(
    websocket: WebSocket,
    match_id: int,
    token: str = Query(...)
):
    """
    WebSocket 实时聊天

    连接方式: ws://host/ws/chat/{match_id}?token=xxx

    消息格式:
    发送: {"content": "你好", "message_type": "text"}
    接收: {"type": "new_message", "message": {...}}
    接收: {"type": "typing", "user_id": 123}
    接收: {"type": "read", "user_id": 123}
    """
    # 验证token
    from minder.api.routers.auth import _verify_token, SECRET_KEY
    payload = _verify_token(token, SECRET_KEY)
    if not payload:
        await websocket.close(code=4001, reason="无效的令牌")
        return

    user_id = payload.get("user_id")
    if not user_id:
        await websocket.close(code=4001, reason="无效的用户")
        return

    # 验证匹配关系
    from minder.db import async_session
    async with async_session() as db:
        result = await db.execute(
            select(Match).where(
                Match.id == match_id,
                or_(Match.user_a_id == user_id, Match.user_b_id == user_id),
                Match.is_mutual == True
            )
        )
        match = result.scalar_one_or_none()
        if not match:
            await websocket.close(code=4003, reason="会话不存在")
            return

        partner_id = match.user_b if match.user_a_id == user_id else match.user_a

    # 注册连接
    await manager.connect(websocket, match_id, user_id)

    # 通知对方上线
    await manager.send_to_user(match_id, partner_id, {
        "type": "online",
        "user_id": user_id,
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_data = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = msg_data.get("type", "message")

            if msg_type == "message":
                content = msg_data.get("content", "").strip()
                if not content:
                    continue

                # 保存消息
                async with async_session() as db:
                    message = Message(
                        match_id=match_id,
                        sender_id=user_id,
                        content=content,
                        message_type=msg_data.get("message_type", "text"),
                        is_read=False,
                    )
                    db.add(message)
                    await db.commit()
                    await db.refresh(message)

                    msg_response = {
                        "type": "new_message",
                        "message": {
                            "id": message.id,
                            "match_id": message.match_id,
                            "sender_id": message.sender_id,
                            "content": message.content,
                            "message_type": message.message_type,
                            "is_read": message.is_read,
                            "created_at": message.created_at.isoformat(),
                        }
                    }

                # 发送给对方
                await manager.send_to_user(match_id, partner_id, msg_response)
                # 确认发送
                await manager.send_to_user(match_id, user_id, {
                    "type": "message_sent",
                    "message_id": msg_response["message"]["id"],
                })

            elif msg_type == "typing":
                await manager.send_to_user(match_id, partner_id, {
                    "type": "typing",
                    "user_id": user_id,
                })

            elif msg_type == "read":
                # 标记消息已读
                async with async_session() as db:
                    await db.execute(
                        Message.__table__.update()
                        .where(
                            Message.match_id == match_id,
                            Message.sender_id == partner_id,
                            Message.is_read == False
                        )
                        .values(is_read=True)
                    )
                    await db.commit()

                await manager.send_to_user(match_id, partner_id, {
                    "type": "read",
                    "user_id": user_id,
                })

    except WebSocketDisconnect:
        manager.disconnect(match_id, user_id)
        await manager.send_to_user(match_id, partner_id, {
            "type": "offline",
            "user_id": user_id,
        })
    except Exception:
        manager.disconnect(match_id, user_id)

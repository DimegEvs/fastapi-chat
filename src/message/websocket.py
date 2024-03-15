import datetime
from typing import Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.message.models import Message, manager
from src.user.models import User, UserService
from src.database import async_session_maker, get_async_session


router = APIRouter(
    prefix="",
    tags=["WS"]
)

@router.websocket("/ws/{sender_id}/{recipient_id}")
async def websocket_endpoint(websocket: WebSocket, sender_id: int, recipient_id: int):
    await manager.connect(sender_id, websocket)
    last_messages = await manager.get_history(manager, sender_id=sender_id, recipient_id=recipient_id)
    for mes in last_messages:
        await manager.send_active_user_message(websocket=websocket, recipient_id=recipient_id, data=mes)
    try:
        while True:
            message = await websocket.receive_json()
            await manager.insert_message_to_datebase(manager, message=message["message"], sender_id = sender_id, recipient_id=recipient_id)
            res = await manager.get_last_message(sender_id=sender_id, recipient_id=recipient_id)
            await manager.send_active_user_message(websocket=websocket, recipient_id=recipient_id, data=res)
    except WebSocketDisconnect:
        manager.disconnect(sender_id, websocket)
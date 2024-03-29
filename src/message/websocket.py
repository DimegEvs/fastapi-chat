import datetime
from typing import Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.message.models import Message, manager
from src.user.models import User, UserService
from src.message.utils import send_notifications
from src.database import async_session_maker, get_async_session


router = APIRouter(
    prefix="",
    tags=["WS"]
)

@router.websocket("/ws/{sender_id}/{recipient_id}")
async def websocket_endpoint(websocket: WebSocket, sender_id: int, recipient_id: int):
    await manager.connect(sender_id=sender_id, websocket=websocket, recipient_id=recipient_id)
    last_messages = await manager.get_history(manager, sender_id=sender_id, recipient_id=recipient_id)
    for mes in last_messages:
        await manager.send_pesonal_message(websocket=websocket, sender_id=sender_id, recipient_id=recipient_id, data=mes)
    try:
        while True:
            message = await websocket.receive_json()
            is_read = (recipient_id in manager.active_connections and (sender_id in manager.active_connections[recipient_id])) 
            await manager.insert_message_to_datebase(manager, message=message["message"], sender_id = sender_id, recipient_id=recipient_id, is_read=is_read)
            res = await manager.get_last_message(sender_id=sender_id, recipient_id=recipient_id)
            await manager.send_active_user_message(websocket=websocket, recipient_id=recipient_id, sender_id=sender_id, data=res)
            if (recipient_id not in manager.active_connections) or (recipient_id in manager.active_connections and (sender_id not in manager.active_connections[recipient_id])):
                await send_notifications(sender_id=sender_id, recipient_id=recipient_id)
    except WebSocketDisconnect:
        manager.disconnect(sender_id, websocket)



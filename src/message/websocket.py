import datetime
from typing import Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.message.models import Message as message_model
from src.message.utils import send_message_to_frontend
from src.database import async_session_maker, get_async_session
router = APIRouter(
    prefix="",
    tags=["WS"]
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, sender_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[sender_id] = websocket

    def disconnect(self, sender_id: int, websocket: WebSocket):
        del self.active_connections[sender_id]

    async def send_personal_message(self, websocket: WebSocket, data):
        await websocket.send_json(data)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
            
    async def send_active_user_message(self, websocket: WebSocket, reciepient_id: int, data):
        if reciepient_id in self.active_connections:
            connection = self.active_connections[reciepient_id]
            await connection.send_json(data=data)
            await websocket.send_json(data=data)
        else:
            await websocket.send_json(data=data)
    
    @staticmethod
    async def instert_message_to_datebase(self, message: str, sender_id: int, reciepient_id: int):
        async with async_session_maker() as session:
            stmt = insert(message_model).values(
                message=message,
                sender_id=sender_id,
                reciepient_id=reciepient_id,
                timestamp=datetime.datetime.now()
            )
            await session.execute(stmt)
            await session.commit()
            
    @staticmethod
    async def get_history(self, sender_id: int, reciepien_id: int):
        async with async_session_maker() as session:
            query = select(message_model).where(
                    or_(
                        and_(message_model.sender_id == sender_id, message_model.reciepient_id == reciepien_id),
                        and_(message_model.sender_id == reciepien_id, message_model.reciepient_id == sender_id)
                    )
                ).order_by(message_model.timestamp)
            result = await session.execute(query)
            messages_dicts = [message[0].to_dict() for message in result]
            return messages_dicts

manager = ConnectionManager()
    
    
@router.websocket("/ws/{sender_id}/{reciepient_id}")
async def websocket_endpoint(websocket: WebSocket, sender_id: int, reciepient_id: int):
    await manager.connect(sender_id, websocket)
    last_messages = await manager.get_history(manager, sender_id=sender_id, reciepien_id=reciepient_id)
    for mes in last_messages:
        await manager.send_personal_message(websocket, mes)
    try:
        while True:
            message = await websocket.receive_json()
            await manager.instert_message_to_datebase(manager, message=message["message"], sender_id = sender_id, reciepient_id=reciepient_id)
            await manager.send_active_user_message(websocket=websocket, reciepient_id=reciepient_id, data={"sender_id": sender_id, "reciepient_id": reciepient_id, "message": message["message"]})
    except WebSocketDisconnect:
        manager.disconnect(sender_id, websocket)
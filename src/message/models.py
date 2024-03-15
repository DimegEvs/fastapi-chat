from ast import Dict
from datetime import datetime

from fastapi_users.db import BaseUserDatabase
from fastapi import Depends, WebSocket
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import (JSON, TIMESTAMP, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Table, and_, func, insert, join, or_, select)

from src.database import Base, async_session_maker
from src.user.models import User

class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    message = Column(String, nullable= False)
    sender_id = Column(Integer, ForeignKey("user.id"))
    recipient_id = Column(Integer, ForeignKey("user.id"))
    timestamp = Column(DateTime, default=func.now())
    is_read = Column(Boolean, default= False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read
        }
        
    class Config:
        from_attributes = True
    


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
            
    async def send_active_user_message(self, websocket: WebSocket, recipient_id: int, data):
        if recipient_id in self.active_connections:
            connection = self.active_connections[recipient_id]
            await connection.send_json(data=data)
            
            await websocket.send_json(data=data)
        else:
            print(data)
            await websocket.send_json(data=data)
    
    @staticmethod
    async def insert_message_to_datebase(self, message: str, sender_id: int, recipient_id: int):
        async with async_session_maker() as session:
            stmt = insert(Message).values(
                message=message,
                sender_id=sender_id,
                recipient_id=recipient_id,
                timestamp=datetime.now()
            )
            await session.execute(stmt)
            await session.commit()
            
    @staticmethod
    async def get_history(self, sender_id: int, recipient_id: int):
        async with async_session_maker() as session:
            query = (
                select(Message, User.name.label('nameSender'), User.surname.label('surnameSender'))
                .select_from(join(Message, User, onclause=Message.sender_id == User.id))
                .where(or_(
                    and_(Message.sender_id == sender_id, Message.recipient_id == recipient_id),
                    and_(Message.sender_id == recipient_id, Message.recipient_id == sender_id)
                ))
                .order_by(Message.timestamp)
            )
            result = await session.execute(query)
            messages_with_user_info = [
                {
                    'message': message[0].to_dict(),
                    'sender_name': f"{message.nameSender} {message.surnameSender}"
                }
                for message in result
            ]
            return messages_with_user_info
    
    @classmethod
    async def get_last_message(self, sender_id: int, recipient_id: int):
        async with async_session_maker() as session:
            query = (
                select(Message, User.name.label('nameSender'), User.surname.label('surnameSender'))
                .select_from(join(Message, User, onclause=Message.sender_id == User.id))
                .where(or_(
                    and_(Message.sender_id == sender_id, Message.recipient_id == recipient_id),
                    and_(Message.sender_id == recipient_id, Message.recipient_id == sender_id)
                ))
                .order_by(Message.timestamp.desc())
            )
            result = await session.execute(query)
            message_with_user_info = result.fetchone()  # Получаем только первый элемент
            if message_with_user_info:
                return {
                    'message': message_with_user_info[0].to_dict(),
                    'sender_name': f"{message_with_user_info.nameSender} {message_with_user_info.surnameSender}"
                }
            else:
                return None


manager = ConnectionManager()
    
from ast import Dict
from datetime import datetime

import httpx
from fastapi import Depends, WebSocket
from fastapi_users.db import BaseUserDatabase
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import (JSON, TIMESTAMP, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Table, and_, func, insert, join, or_, select, update)

from src.config import URL_LOGGER
from src.database import Base, async_session_maker
from src.user.models import User


# Определение модели сообщения
class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)  # Уникальный идентификатор сообщения
    message = Column(String, nullable=False)  # Текст сообщения
    sender_id = Column(Integer, ForeignKey("user.id"))  # Идентификатор отправителя
    recipient_id = Column(Integer, ForeignKey("user.id"))  # Идентификатор получателя
    timestamp = Column(DateTime, default=func.now())  # Время отправки сообщения
    is_read = Column(Boolean, default=False)  # Статус прочтения сообщения

    def to_dict(self):
        # Преобразование объекта сообщения в словарь
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read
        }

    class Config:
        from_attributes = True  # Настройка конфигурации для использования атрибутов


# Класс для управления подключениями WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}  # Словарь активных подключений

    async def connect(self, sender_id: int, recipient_id: int, websocket: WebSocket):
        await websocket.accept()  # Принятие WebSocket соединения
        self.active_connections[sender_id] = [recipient_id, websocket]  # Сохранение подключения
        await self.update_messages_to_datebase(self=self, sender_id=recipient_id,
                                               recipient_id=sender_id)  # Обновление статуса сообщений

    def disconnect(self, sender_id: int, websocket: WebSocket):
        del self.active_connections[sender_id]  # Удаление подключения

    async def send_pesonal_message(self, websocket: WebSocket, recipient_id: int, sender_id: int, data):
        await websocket.send_json(data=data)  # Отправка личного сообщения

    async def send_active_user_message(self, websocket: WebSocket, recipient_id: int, sender_id: int, data):
        try:
            params = {
                "type": "INFO",
                "user_id": sender_id,
                "message": f"User ID: {sender_id} send message TEXT: {data['message']['message']} to ID: {recipient_id}."
            }
            async with httpx.AsyncClient() as client:
                if recipient_id in manager.active_connections and sender_id in manager.active_connections[recipient_id]:
                    connection = self.active_connections[recipient_id]
                    await connection[1].send_json(data=data)  # Отправка сообщения активному пользователю
                    await websocket.send_json(data=data)
                    await client.get(URL_LOGGER, params=params)  # Логирование
                else:
                    await websocket.send_json(data=data)
                    await client.get(URL_LOGGER, params=params)
        except KeyError:
            print("Пользователь не найден")  # Обработка ошибки, если пользователь не найден

    @staticmethod
    async def update_messages_to_datebase(self, sender_id: int, recipient_id: int):
        async with async_session_maker() as session:
            stmt = update(Message).where(
                and_(Message.recipient_id == recipient_id, Message.sender_id == sender_id)).values(is_read=True)
            await session.execute(stmt)  # Обновление статуса сообщений в базе данных
            await session.commit()

    @staticmethod
    async def insert_message_to_datebase(self, message: str, sender_id: int, recipient_id: int, is_read: bool):
        async with async_session_maker() as session:
            stmt = insert(Message).values(
                message=message,
                sender_id=sender_id,
                recipient_id=recipient_id,
                timestamp=datetime.now(),
                is_read=is_read
            )
            await session.execute(stmt)  # Вставка нового сообщения в базу данных
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
            result = await session.execute(query)  # Получение истории сообщений между пользователями
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
            result = await session.execute(query)  # Получение последнего сообщения между пользователями
            message_with_user_info = result.fetchone()  # Получаем только первый элемент
            if message_with_user_info:
                return {
                    'message': message_with_user_info[0].to_dict(),
                    'sender_name': f"{message_with_user_info.nameSender} {message_with_user_info.surnameSender}"
                }
            else:
                return None


# Инициализация менеджера подключений
manager = ConnectionManager()

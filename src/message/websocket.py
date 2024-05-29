import datetime
import httpx
from typing import Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, insert, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.message.models import Message, manager
from src.config import URL_MIDDLEWARE
from src.user.models import User, UserService
from src.message.utils import send_notifications
from src.database import async_session_maker, get_async_session

# Создание роутера для WebSocket с тегом "WS"
router = APIRouter(
    prefix="",
    tags=["WS"]
)

# Обработчик для WebSocket соединения
@router.websocket("/ws/{sender_id}/{recipient_id}")
async def websocket_endpoint(websocket: WebSocket, sender_id: int, recipient_id: int):
    await manager.connect(sender_id=sender_id, websocket=websocket, recipient_id=recipient_id)  # Подключение пользователя к WebSocket

    # Параметры для логирования подключения
    params = {
        "message": f"Websocket accepted: {websocket.url} IP: {websocket.client.host} HEADERS: {websocket.headers} COOKIES: {websocket.cookies}"
    }

    # Логирование подключения через HTTP запрос
    async with httpx.AsyncClient() as client:
        try:
            await client.get(URL_MIDDLEWARE, params=params)
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    # Получение истории сообщений
    last_messages = await manager.get_history(manager, sender_id=sender_id, recipient_id=recipient_id)
    for mes in last_messages:
        await manager.send_pesonal_message(websocket=websocket, sender_id=sender_id, recipient_id=recipient_id, data=mes)  # Отправка истории сообщений пользователю

    try:
        while True:
            message = await websocket.receive_json()  # Получение нового сообщения от WebSocket клиента

            # Параметры для логирования отправки сообщения
            params = {
                "message": f"Websocket send_message: {websocket.url} IP: {websocket.client.host} HEADERS: {websocket.headers} COOKIES: {websocket.cookies} MESSAGE: {message}"
            }

            # Логирование отправки сообщения через HTTP запрос
            async with httpx.AsyncClient() as client:
                try:
                    await client.get(URL_MIDDLEWARE, params=params)
                except httpx.HTTPError as e:
                    print(f"HTTP error occurred: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

            # Проверка, прочитано ли сообщение
            is_read = (recipient_id in manager.active_connections and (sender_id in manager.active_connections[recipient_id]))

            # Вставка нового сообщения в базу данных
            await manager.insert_message_to_datebase(manager, message=message["message"], sender_id=sender_id, recipient_id=recipient_id, is_read=is_read)

            # Получение последнего сообщения и отправка его пользователям
            res = await manager.get_last_message(sender_id=sender_id, recipient_id=recipient_id)
            await manager.send_active_user_message(websocket=websocket, recipient_id=recipient_id, sender_id=sender_id, data=res)

            # Отправка уведомления, если получатель не в сети или диалоге с отправителем
            if (recipient_id not in manager.active_connections) or (recipient_id in manager.active_connections and (sender_id not in manager.active_connections[recipient_id])):
                await send_notifications(sender_id=sender_id, recipient_id=recipient_id)
    except WebSocketDisconnect:
        # Параметры для логирования отключения
        params = {
            "message": f"Websocket disconnected: {websocket.url} IP: {websocket.client.host} HEADERS: {websocket.headers} COOKIES: {websocket.cookies}"
        }

        # Логирование отключения через HTTP запрос
        async with httpx.AsyncClient() as client:
            try:
                await client.get(URL_MIDDLEWARE, params=params)
            except httpx.HTTPError as e:
                print(f"HTTP error occurred: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        # Отключение пользователя от WebSocket
        manager.disconnect(sender_id, websocket)

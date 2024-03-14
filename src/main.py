from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import requests
from src.message.utils import send_message_to_frontend
from src.message.websocket import router as router_websocket
app = FastAPI()

# Моковые данные для примера
mock_chats = {
    (1, 2): [
        {"sender": 1, "message": "Привет!"},
        {"sender": 2, "message": "Привет, как дела?"},
        {"sender": 1, "message": "Все хорошо, спасибо!"},
    ],
    (2, 1): [
        {"sender": 2, "message": "Привет!"},
        {"sender": 1, "message": "Привет, как дела?"},
        {"sender": 2, "message": "Все хорошо, спасибо!"},
    ],
}


app.include_router(router_websocket)
# Словарь для хранения активных WebSocket-соединений
# active_connections: List[WebSocket] = []

# @app.websocket("/ws/{sender}/{recipient}")
# async def websocket_endpoint(websocket: WebSocket, sender: int, recipient: int):
#     await websocket.accept()
#     active_connections.append(websocket)

#     try:
#         # ... (код для отправки истории чата)

#         while True:
#             # Получаем новое сообщение от клиента
#             data = await websocket.receive_json()
#             message = {"sender": sender, "message": data["message"]}
#             print(message)
#             # Сохраняем сообщение в моковой истории чата
#             key = (sender, recipient)
#             if key not in mock_chats:
#                 mock_chats[key] = []
#             mock_chats[key].append(message)

#             # Отправляем новое сообщение всем активным соединениям
#             for connection in active_connections:
#                 await connection.send_json(message)

#             # Отправляем новое сообщение на localhost:8000
#             send_message_to_frontend(sender, recipient, data["message"])
#     except WebSocketDisconnect:
#         print()
#         active_connections.remove(websocket)

# # Функция для отправки сообщения на localhost:8000

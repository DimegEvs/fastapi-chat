import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from typing import List
from src.message.websocket import router as router_websocket

# Создание приложения FastAPI
app = FastAPI()

# Подключение маршрутов WebSocket
app.include_router(router_websocket)


# Определение промежуточного ПО для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Параметры для логирования запроса
    params = {
        "message": f"Request: {request.method} {request.url} IP: {request.client.host} HEADERS: {request.headers} COOKIES: {request.cookies}"
    }
    # Логирование запроса через HTTP запрос
    async with httpx.AsyncClient() as client:
        try:
            await client.get(URL_MIDDLEWARE, params=params)
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    # Вызов следующего обработчика запроса
    response = await call_next(request)
    return response

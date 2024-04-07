import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from typing import List
import requests
from src.message.websocket import router as router_websocket
app = FastAPI()

app.include_router(router_websocket)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    params = {
        "message": f"Request: {request.method} {request.url} IP: {request.client.host} HEADERS: {request.headers} COOKIES: {request.cookies}"
    }
    async with httpx.AsyncClient() as client:
        try:
            response1 = await client.get(URL_MIDDLEWARE, params=params)
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    response = await call_next(request)
    return response

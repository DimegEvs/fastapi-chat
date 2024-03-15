from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import requests
from src.message.websocket import router as router_websocket
app = FastAPI()

app.include_router(router_websocket)


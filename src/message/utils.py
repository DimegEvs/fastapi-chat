from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import requests


def send_message_to_frontend(sender_id: int, reciepient_id: int, message: str):
    url = f"http://127.0.0.1:8000/message/receive_message/{sender_id}/{reciepient_id}"
    payload = {"message": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to frontend: {e}")
        

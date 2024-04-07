


import requests


async def send_notifications(sender_id: int, recipient_id: int):
    url = f"http://fastapi-noti:8002/ws_forward/{recipient_id}/{sender_id}"
    response = requests.get(url)
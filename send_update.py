import requests
from tokenbot import BASE_URL

def get_updates(offset=None):
    url = BASE_URL + "getUpdates"
    params = {"offset": offset}
    response = requests.get(url, params=params)
    return response.json().get("result", [])

def send_message(chat_id, text):
    url = BASE_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)
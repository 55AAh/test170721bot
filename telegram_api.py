import os
from time import sleep

import requests


class TelegramApi:
    def __init__(self, bot_token=os.getenv("TG_BOT_TOKEN")):
        self._bot_token = bot_token

    def _request(self, method, params=None):
        response = requests.get(f"https://api.telegram.org/bot{self._bot_token}/{method}", params=params)
        response_json = response.json()
        assert response_json["ok"], f"Bad response: {response_json}"
        result = response_json["result"]
        return result

    def get_updates(self, offset=None, timeout=None):
        return self._request("getUpdates", params={"offset": offset, "timeout": timeout})

    def set_webhook(self, url):
        return self._request("setWebhook", params={"url": url, "max_connections": 1})

    def send_text(self, chat_id, text, reply_to_message_id=None, allow_sending_without_reply=True):
        response = self._request("sendMessage", params={"chat_id": chat_id, "text": text,
                                                        "reply_to_message_id": reply_to_message_id,
                                                        "allow_sending_without_reply": allow_sending_without_reply})
        sleep(3)
        return response

    def echo_text(self, msg):
        return self.send_text(chat_id=msg["chat"]["id"], text=msg["text"], reply_to_message_id=msg["message_id"])

import os
from time import time, sleep
import requests

from logs import Logger


class TelegramApi:
    def __init__(self, bot_token=os.getenv("TG_BOT_TOKEN")):
        self._bot_token = bot_token
        self.log = Logger.get_logger("TG_API")
        self.idle_until = None

    def idle(self):
        self.log.warning("Idling...")
        sleep(1)
        return time() <= self.idle_until

    def _request(self, method, params=None):
        response = requests.get(f"https://api.telegram.org/bot{self._bot_token}/{method}", params=params)
        response_json = response.json()
        if not response_json["ok"] and response_json["error_code"] == 429:
            sleep_time = response_json["parameters"]["retry_after"]
            self.log.warning(f"Too many requests, sleeping for {sleep_time}s...")
            self.idle_until = time() + sleep_time
            return None
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
        # sleep(1)
        return response

    def echo_text(self, msg):
        return self.send_text(chat_id=msg["chat"]["id"], text=msg["text"], reply_to_message_id=msg["message_id"])

import os
from time import time, sleep
import requests

from logs import Logger


class TelegramApi:
    def __init__(self, bot_token=os.getenv("TG_BOT_TOKEN")):
        self._bot_token = bot_token
        self.log = Logger.get_logger("TG_API")
        self.sent_timestamps = []

    def _request(self, method, params=None):
        response = requests.get(f"https://api.telegram.org/bot{self._bot_token}/{method}", params=params)
        response_json = response.json()
        if not response_json["ok"]:
            error_code = response_json["error_code"]
            if error_code == 429:
                sleep_time = response_json["parameters"]["retry_after"]
                self.log.warning(f"Too many requests, sleeping for {sleep_time}s...")
                idle_until = time() + sleep_time
                while time() <= idle_until:
                    yield
                    sleep(1)
                result = yield from self._request(method, params=params)
                return result
            elif error_code == 409:
                self.log.warning(f"Webhook was not cleared before getUpdates")
                yield from self.clear_webhook()
                return self._request(method, params=params)
        assert response_json["ok"], f"Bad response: {response_json}"
        result = response_json["result"]
        return result

    def get_updates(self, offset=None, timeout=None):
        return self._request("getUpdates", params={"offset": offset, "timeout": timeout})

    def set_webhook(self, url):
        return self._request("setWebhook", params={"url": url, "max_connections": 1})

    def clear_webhook(self):
        return self.set_webhook(url=None)

    def send_message(self, msg):
        while len(self.sent_timestamps) >= 20:
            if time() - self.sent_timestamps[0] > 60:
                del self.sent_timestamps[0]
            sleep(1)
            yield
        if self.sent_timestamps:
            sleep(max(0, 2 - (time() - self.sent_timestamps[-1])))
        result = yield from self._request("sendMessage", params=msg)
        self.sent_timestamps.append(time())
        return result

    def send_text(self, chat_id, text, reply_to_message_id=None, allow_sending_without_reply=True):
        return self.send_message(msg={"chat_id": chat_id, "text": text,
                                      "reply_to_message_id": reply_to_message_id,
                                      "allow_sending_without_reply": allow_sending_without_reply})

    def echo_text(self, msg):
        return self.send_text(chat_id=msg["chat"]["id"], text=msg["text"], reply_to_message_id=msg["message_id"])

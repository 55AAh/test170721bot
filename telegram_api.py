from time import time, sleep
import requests

from logs import Logger


class TelegramApiRequest:
    def __init__(self, api, method, params=None, is_send=False):
        self._api = api
        self._method = method
        self._params = params
        self._is_send = is_send

    def __call__(self, *args):
        if self._is_send:
            yield from self._api._send_flood_controller.wait()
        response = requests.get(f"https://api.telegram.org/bot{self._api._bot_token}/{self._method}",
                                params=self._params)
        if self._is_send:
            self._api._send_flood_controller.send()
        response_json = response.json()
        if not response_json["ok"]:
            error_code = response_json["error_code"]
            if error_code == 429:
                sleep_time = response_json["parameters"]["retry_after"]
                self._api._log.warning(f"Too many requests, sleeping for {sleep_time}s...")
                idle_until = time() + sleep_time
                while time() <= idle_until:
                    yield True
                    sleep(1)
                result = yield from self(*args)
                return result
            elif error_code == 409:
                self._api._log.warning(f"Webhook was not cleared before getUpdates")
                yield from self._api.clear_webhook()
                return self(*args)
        assert response_json["ok"], f"Bad response: {response_json}"
        result = response_json["result"]
        return result

    def _block_complete(self):
        gen = self()
        try:
            while True:
                next(gen)
        except StopIteration as e:
            return e.value


class _SendFloodController:
    def __init__(self):
        self.sent_timestamps = []

    def wait(self):
        while len(self.sent_timestamps) >= 20:
            if time() - self.sent_timestamps[0] > 60:
                del self.sent_timestamps[0]
            sleep(1)
            yield True
        if self.sent_timestamps:
            sleep(max(0, 2 - (time() - self.sent_timestamps[-1])))
        yield True

    def send(self):
        self.sent_timestamps.append(time())


class TelegramApi:
    def __init__(self, bot_token, request_class=TelegramApiRequest):
        self._bot_token = bot_token
        self._request_class = request_class
        self.log = Logger.get_logger("TG_API")
        self._send_flood_controller = _SendFloodController()

    def get_updates(self, offset=None, timeout=None):
        return self._request_class(self, "getUpdates", params={"offset": offset, "timeout": timeout})

    def set_webhook(self, url):
        return self._request_class(self, "setWebhook", params={"url": url, "max_connections": 1})

    def clear_webhook(self):
        return self.set_webhook(url=None)

    def send_message(self, msg):
        return self._request_class(self, "sendMessage", params=msg, is_send=True)

    def send_text(self, chat_id, text, reply_to_message_id=None, allow_sending_without_reply=True):
        return self.send_message(msg={"chat_id": chat_id, "text": text,
                                      "reply_to_message_id": reply_to_message_id,
                                      "allow_sending_without_reply": allow_sending_without_reply})

    def echo_text(self, msg, at):
        return self.send_text(chat_id=msg["chat"]["id"],
                              text=at + " " + msg["text"],
                              reply_to_message_id=msg["message_id"])

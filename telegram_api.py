import os
import requests


class TelegramApi:
    def __init__(self, bot_token=os.getenv("TG_BOT_TOKEN")):
        self._bot_token = bot_token

    def _request(self, method, params=None):
        response = requests.get(f"https://api.telegram.org/bot{self._bot_token}/{method}", params=params)
        response_json = response.json()
        assert response_json["ok"]
        result = response_json["result"]
        return result

    def get_updates(self, offset=None, timeout=None):
        return self._request("getUpdates", params={"offset": offset, "timeout": timeout})

from logs import Logger


class Bot:
    def __init__(self, server, db, tg_api):
        self.server = server
        self.db = db
        self.tg_api = tg_api
        self.log = Logger.get_logger("BOT")

    def handle_update(self, update):
        self.log.info(f"\tUPDATE TEXT: {update.setdefault('message', {}).setdefault('text', None)}")
        if not self.server.call_tg_api(self.tg_api.echo_text, update["message"]):
            return

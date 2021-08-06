from logs import Logger


class Bot:
    def __init__(self, db, tg_api):
        self.db = db
        self.tg_api = tg_api
        self.log = Logger.get_logger("BOT")

    def handle_tg_update(self, update):
        self.log.info(f"\tUPDATE TEXT: {update.setdefault('message', {}).setdefault('text', None)}")
        yield from self.tg_api.echo_text(update["message"])
        self.log.info(f"\tUPDATE HANDLED")

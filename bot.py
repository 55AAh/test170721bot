from logs import Logger


class Bot:
    def __init__(self, db, tg_api):
        self.db = db
        self.tg_api = tg_api
        self.log = Logger.get_logger("BOT")

    def handle_tg_update(self, update):
        self.db.save_update(update)
        self.log.info(f"{update.setdefault('message', {}).setdefault('text', None)}")
        yield

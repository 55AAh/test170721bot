from os import getenv


class Environment:
    HEROKU_LINK = None
    DATABASE_URL = None
    TG_BOT_TOKEN = None
    LOG_LEVEL = None
    LOG_FORMAT = None

    @classmethod
    def initialize(cls):
        cls.HEROKU_LINK = getenv("HEROKU_LINK")
        cls.DATABASE_URL = getenv("DATABASE_URL")
        cls.TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")
        cls.LOG_LEVEL = getenv("LOG_LEVEL", "INFO")
        cls.LOG_FORMAT = getenv("LOG_FORMAT", '%(asctime)s %(levelname)-8s %(processName)-15s %(name)-15s %(message)s')


if __name__ == 'environment':
    Environment.initialize()

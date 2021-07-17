import logging
from logging import DEBUG as DEBUG

class Logger:
    def __init__(self, file_path):
        log_formatter = logging.Formatter(
            # "%(asctime)s %(levelname)6s [%(name)10s %(filename)10s:%(lineno)5s %(funcName)15s] %(message)s")
            "%(asctime)s %(levelname)6s [%(funcName)15s] %(message)s")

        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.NOTSET)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)


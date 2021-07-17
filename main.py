from logging import log, INFO
import os

from logger import Logger
from server import Server


def main():
    Logger("log.txt")
    log(INFO, "\tSTARTING...")

    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 80))
    server = Server(HOST, PORT)
    server.start()


if __name__ == '__main__':
    main()

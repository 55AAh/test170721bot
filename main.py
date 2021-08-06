import multiprocessing

from logs import Logger
from server import Server


def main():
    Logger.setup()
    Logger.start_listener()

    server = Server()
    server.run()

    Logger.stop_listener()


if __name__ == '__main__':
    multiprocessing.set_start_method("spawn", force=True)
    print("> APP STARTED <")
    main()
    print("> APP STOPPED <")

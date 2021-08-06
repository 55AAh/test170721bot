import os
from multiprocessing import Pipe, connection
from signal import SIGTERM, signal
from time import sleep

from pipe_component import DuplexPipeComponent
from worker_process import WorkerProcess, Worker
from telegram_api import TelegramApi
from db import Db
from webserver import Webserver, BackendAPI
from bot import Bot
from logs import Logger, LoggingComponent

__all__ = ["Server"]


def _signal_stopper(log, event):
    sleep(10)
    log.error("Caught SIGTERM")
    event.send(None)


class Server:
    def __init__(self):
        self.log = Logger.get_logger("SERVER")
        self.webhook_log = Logger.get_logger("WEBHOOK")
        self.db = Db()
        self.tg_api = TelegramApi()
        self.poller = _PollerProcess()
        self.webserver = Webserver()
        self.bot = Bot(self, self.db, self.tg_api)
        self.last_update_id = None
        self.stop_event, self._remote_stop_event = None, None

    def _register_signal_handler(self):
        receiver, sender = Pipe(duplex=False)
        self.stop_event = receiver
        self._remote_stop_event = sender

        def on_sigterm(_signal_number, _frame):
            self.log.info("Caught SIGTERM")
            self._remote_stop_event.send(None)

        # Process(target=_signal_stopper, args=(self.log, self._remote_stop_event), daemon=True).start()

        signal(SIGTERM, on_sigterm)

    def run(self):
        self.db.connect()

        self.clear_webhook()
        self._register_signal_handler()
        self.log.info("Started")

        self.poller.start(self.tg_api, timeout=90)

        self.last_update_id = self.db.last_update_id
        self.poller.worker.pipe.send(self.last_update_id)

        self.webserver.start()

        try:
            while not self.stop_event.poll():
                connection.wait([self.poller.worker.pipe, self.webserver.api_pipe, self.stop_event])
                self.handle_update()
                self.handle_web_api_request()
        except KeyboardInterrupt:
            pass

        self.poller.stop()
        self.webserver.stop()
        self.poller.join()
        self.webserver.join()
        self.log.info("Saving data to db...")
        self.db.last_update_id = self.last_update_id
        self.db.disconnect()
        self.log.info("Data saved, stopped")
        self.set_webhook()

    def handle_update(self):
        pipe = self.poller.worker.pipe
        if not pipe.poll() or self.stop_event.poll():
            return
        update = pipe.recv()
        if update:
            self.bot.handle_update(update)
            if self.stop_event.poll():
                return
            self.last_update_id = update["update_id"]
        else:
            pipe.send(self.last_update_id)

    def call_tg_api(self, function, *args, **kwargs):
        while not self.stop_event.poll():
            result = function(*args, **kwargs)
            if result is not None:
                return result
            while not self.stop_event.poll():
                self.handle_web_api_request()
                if not self.tg_api.idle():
                    break

    def handle_web_api_request(self):
        pipe = self.webserver.api_pipe
        if not pipe.poll() or self.stop_event.poll():
            return
        request = pipe.recv()
        self.log.info(f"web api request: {request}")
        response = BackendAPI.handle(self, request)
        pipe.send(response)

    def clear_webhook(self):
        self.tg_api.clear_webhook()
        self.webhook_log.info("Cleared")

    def set_webhook(self):
        heroku_link = os.getenv("HEROKU_LINK")
        if heroku_link:
            heroku_link += "api/ping"
            self.tg_api.set_webhook(url=heroku_link)
        self.webhook_log.info("Set")


class _PollerProcess(WorkerProcess):
    def __init__(self):
        super().__init__(w_class=_PollerWorker, name="Poller", daemon=True, ignore_sigterm=True)

    def stop(self):
        self.kill()
        Logger.get_logger("POLLER").debug("Stopped")


class _PollerWorker(DuplexPipeComponent, LoggingComponent, Worker):
    def run(self, tg_api: TelegramApi, timeout=90):
        log = self.get_logger("POLLER")
        log.debug("Started")
        while True:
            offset = self.pipe.recv() + 1
            log.debug(f"Polling ({offset})...")
            updates = tg_api.get_updates(offset=offset, timeout=timeout)
            for update in updates:
                self.pipe.send(update)
            self.pipe.send(None)

import os
import pickle
from multiprocessing import Pipe, connection
from signal import SIGTERM, signal
from time import sleep

from pipe_component import DuplexPipeComponent
from telegram_api import TelegramApi
from worker_process import WorkerProcess, Worker
from webserver import Webserver, BackendAPI
from logs import Logger, LoggingComponent

__all__ = ["Server"]


def _signal_stopper(log, event):
    sleep(10)
    log.error("Caught SIGTERM")
    event.send(None)


class Server:
    def __init__(self, bot):
        self.poller = _PollerProcess()
        self.webserver = Webserver()
        self.bot = bot
        self.db = bot.db
        self.tg_api = bot.tg_api
        self.last_update_id = None
        self.stop_event, self._remote_stop_event = None, None
        self.finish = False
        self.log = Logger.get_logger("SERVER")
        self.webhook_log = Logger.get_logger("WEBHOOK")

    def _register_signal_handler(self):
        receiver, sender = Pipe(duplex=False)
        self.stop_event = receiver
        self._remote_stop_event = sender

        def on_sigterm(_signal_number, _frame):
            self.log.info("Caught SIGTERM")
            self._remote_stop_event.send(None)

        signal(SIGTERM, on_sigterm)

    def run(self):
        self.webserver.start()
        self.db.connect()

        self.clear_webhook()
        self._register_signal_handler()
        self.log.info("Started")

        self.poller.start(self.tg_api, timeout=90)

        self.log.info("Loading state from db...")
        self.bot.current_promise = pickle.loads(self.db.current_promise)
        self.last_update_id = self.db.last_update_id
        self.log.info("State loaded")

        tg_update = self.handle_tg_updates()
        web_api_request = self.handle_web_api_requests()
        stoppable = True
        while not self.stop_event.poll() or not stoppable:
            connection.wait([self.poller.worker.pipe, self.webserver.api_pipe, self.stop_event])
            if not self.finish or self.bot.current_promise:
                self.log.debug("ACTION =", stoppable) if (stoppable := next(tg_update)) else None
            elif self.poller.worker.pipe.poll():
                self.poller.worker.pipe.recv()
            next(web_api_request)

        self.poller.stop()
        self.webserver.stop()
        self.poller.join()
        self.webserver.join()

        self.log.info("Saving state to db...")
        self.db.current_promise = pickle.dumps(self.bot.current_promise)
        self.db.last_update_id = self.last_update_id
        self.db.disconnect()
        self.log.info("State saved")

        self.set_webhook()

    def handle_tg_updates(self):
        yield from self.bot._continue_handling_tg_update()

        pipe = self.poller.worker.pipe
        assert pipe.recv() is None
        pipe.send(self.last_update_id)
        yield "Waiting for updates"

        while True:
            while pipe.poll():
                update = pipe.recv()
                if update:
                    print("BEGIN UPDATE")
                    self.last_update_id = update["update_id"]
                    yield from self.bot._handle_tg_update(update)
                    print("END UPDATE")
                    yield "End update"
                else:
                    pipe.send(self.last_update_id)
            yield "End poll"

    def handle_web_api_requests(self):
        pipe = self.webserver.api_pipe
        while True:
            while pipe.poll():
                request = pipe.recv()
                self.log.info(f"web api request: {request}")
                response = BackendAPI.handle(self, request)
                pipe.send(response)
                yield
            yield

    def clear_webhook(self):
        self.tg_api.clear_webhook()._block_complete()
        self.webhook_log.info("Cleared")

    def set_webhook(self):
        heroku_link = os.getenv("HEROKU_LINK")
        if heroku_link:
            heroku_link += "api/webhook"
            self.tg_api.set_webhook(url=heroku_link)._block_complete()
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
            self.pipe.send(None)
            offset = self.pipe.recv() + 1
            log.debug(f"Polling ({offset})...")
            updates = tg_api.get_updates(offset=offset, timeout=timeout)._block_complete()
            for update in updates:
                self.pipe.send(update)

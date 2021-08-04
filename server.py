from multiprocessing import Pipe, connection
from signal import SIGTERM, signal
from time import sleep

from event_component import EventComponent
from pipe_component import DuplexPipeComponent
from worker_process import WorkerProcess, Worker
from telegram_api import TelegramApi
from db import Db
from webserver import Webserver, BackendAPI
from logs import Logger, LoggingComponent

__all__ = ["Server"]


def _signal_stopper(log, event):
    sleep(10)
    log.error("Caught SIGTERM")
    event.send(None)


class Server:
    def __init__(self):
        self.log = None
        self.webhook_log = None
        self.tg_api = TelegramApi()
        self.db = Db()
        self.poller = _PollerProcess()
        self.webserver = Webserver()
        self.last_update_id = None
        self.stop_event, self._remote_stop_event = None, None

    def _register_signal_handler(self):
        receiver, sender = Pipe(duplex=False)
        self.stop_event = receiver
        self._remote_stop_event = sender

        def on_sigterm():
            self.log.info("Caught SIGTERM")
            self._remote_stop_event.send(None)

        # Process(target=_signal_stopper, args=(self.log, self._remote_stop_event), daemon=True).start()

        signal(SIGTERM, on_sigterm)

    def run(self):
        self.log = Logger.get_logger("SERVER")
        self.webhook_log = Logger.get_logger("WEBHOOK")
        self.clear_webhook()
        self._register_signal_handler()
        self.log.info("Started")

        self.db.connect()
        self.poller.start(self.tg_api, timeout=90)

        self.last_update_id = self.db.last_update_id
        self.poller.worker.pipe.send(self.last_update_id)

        self.webserver.start()

        try:
            while not self.stop_event.poll():
                connection.wait([self.poller.worker.pipe, self.webserver.api_pipe, self.stop_event])
                self.handle_updates()
                self.handle_api_request()
        except KeyboardInterrupt:
            pass

        self.log.info("Stopping, saving data to db...")
        self.db.last_update_id = self.last_update_id
        self.log.info("Data saved")
        if self.poller.is_alive():
            self.log.info("Terminating poller...")
        self.poller.stop()
        self.poller.join()
        self.db.disconnect()
        self.log.info("Stopped")
        self.set_webhook()

    def handle_updates(self):
        pipe = self.poller.worker.pipe
        while pipe.poll() and not self.stop_event.poll():
            update = pipe.recv()
            if update:
                self.handle_update(update)
            else:
                pipe.send(self.last_update_id)

    def handle_update(self, update: dict):
        self.log.info(f"\tUPDATE TEXT: {update.setdefault('message', {}).setdefault('text', None)}")
        self.last_update_id = update["update_id"]

    def handle_api_request(self):
        pipe = self.webserver.api_pipe
        if not pipe.poll() or self.stop_event.poll():
            return
        request = pipe.recv()
        self.log.info(f"api request: {request}")
        response = BackendAPI.handle(self, request)
        pipe.send(response)

    def clear_webhook(self):
        self.webhook_log.info("Clearing...")
        self.webhook_log.info("Cleared")

    def set_webhook(self):
        self.webhook_log.info("Setting...")
        self.webhook_log.info("Set")


class _PollerProcess(WorkerProcess):
    def __init__(self):
        super().__init__(w_class=_PollerWorker, name="Poller", daemon=True)

    def stop(self):
        self.terminate()


class _PollerWorker(EventComponent, DuplexPipeComponent, LoggingComponent, Worker):
    def run(self, tg_api: TelegramApi, timeout=90):
        log = self.get_logger("POLLER")
        log.debug("Started")
        while not self.event.set():
            offset = self.pipe.recv() + 1
            log.info(f"Polling ({offset})...")
            updates = tg_api.get_updates(offset=offset, timeout=timeout)
            for update in updates:
                self.pipe.send(update)
            self.pipe.send(None)
        log.debug("Stopped")

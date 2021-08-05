from multiprocessing import Process
from signal import signal, SIGTERM

__all__ = ["Worker", "WorkerProcess"]


class Worker:
    def serialize(self):
        return self.__class__

    def run(self, *args, **kwargs):
        pass


class WorkerProcess(Process):
    def __init__(self, w_class, name: str = None, daemon: bool = None, ignore_sigterm: bool = False):
        super().__init__(name=name, daemon=daemon, target=self._process_main)
        self._ignore_sigterm = ignore_sigterm
        self.worker = w_class()

    _args: tuple[bool, type, tuple, dict]

    def start(self, *args, **kwargs):
        self._args = (self._ignore_sigterm, self.worker.serialize(), args, kwargs)
        super().start()

    def join(self, timeout=None):
        super().join(timeout)
        self.worker = None

    @staticmethod
    def _process_main(ignore_sigterm: bool, s_worker, args, kwargs):
        if ignore_sigterm:
            signal(SIGTERM, lambda _signal_number, _frame: None)
        w: Worker = s_worker()
        w.run(*args, **kwargs)

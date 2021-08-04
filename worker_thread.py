from threading import Thread

__all__ = ["Worker", "WorkerThread"]


class Worker:
    def serialize(self):
        return self.__class__

    def run(self, *args, **kwargs):
        pass


class WorkerThread(Thread):
    def __init__(self, w_class, name: str = None, daemon: bool = None):
        super().__init__(name=name, daemon=daemon, target=self._thread_main)
        self.worker = w_class()

    _args: tuple[type, tuple, dict]

    def start(self, *args, **kwargs):
        self._args = (self.worker.serialize(), args, kwargs)
        super().start()

    def join(self, timeout=None):
        super().join(timeout)
        self.worker = None

    @staticmethod
    def _thread_main(s_worker, args, kwargs):
        w: Worker = s_worker()
        w.run(*args, **kwargs)

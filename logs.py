import logging
import logging.config
import sys
import multiprocessing
from copy import deepcopy

from worker_process import WorkerProcess, Worker
from serialized_class import component

__all__ = ["Logger", "LoggingComponent"]


class Logger:
    @staticmethod
    def get_logger(name=None):
        """ Gets logger by name (creates new if necessary). """
        return logging.getLogger(name)

    @staticmethod
    def setup(config={}):
        """ Setups logging system for current process and child processes started between this and next calls.
        By default it will work without listener (by streaming directly to process' stdout). """
        for handler in logging.getLogger().handlers:
            logging.getLogger().removeHandler(handler)
        Logger._CURRENT_CONFIG = config
        config = deepcopy(config)
        config.setdefault('formatters', {})
        config.setdefault('handlers', {})
        if not config['formatters']:
            config['formatters'] = {
                'default': {
                    'class': 'logging.Formatter',
                    'format': '%(asctime)s %(levelname)-8s %(processName)-15s %(name)-15s %(message)s'
                }
            }
            for h in config['handlers'].keys():
                config['handlers'][h]['formatter'] = 'bypass'
        if not config['handlers']:
            config['handlers'] = {
                'default': {
                    'class': 'logging.StreamHandler',
                    'stream': sys.stdout,
                    'formatter': list(config['formatters'].keys())[0],
                    'level': 'DEBUG',
                }
            }
        config.setdefault("root", {
            'handlers': list(config['handlers'].keys()),
            'level': 'DEBUG'
        })
        config.setdefault('version', 1)
        config.setdefault('disable_existing_loggers', False)
        logging.config.dictConfig(config)
        multiprocessing.get_logger().setLevel(logging.WARNING)
        multiprocessing.get_logger().propagate = True

    @staticmethod
    def start_listener():
        """ Starts listener process. It will receive logs from other processes via pipe and pass them to current
        process' handler.
        All processes (inherited from LoggingComponent) started after this call will be bound to listener.
        Caller process will also be bound. (It should not be inherited from LoggingComponent.) """
        if Logger._LISTENER_ACTIVE:
            return
        Logger.get_logger("LOG_LISTENER").debug("Starting...")
        if Logger._LISTENER is None:
            Logger._LISTENER = _LogListenerProcess()
            Logger._PIPE_HANDLER = Logger._LISTENER.handler
        Logger._LISTENER.start(Logger._CURRENT_CONFIG)
        Logger._LISTENER_ACTIVE = True
        Logger.__deserialize_setup__(Logger.__serialize_setup__())
        Logger.get_logger("LOG_LISTENER").debug("Started")

    @staticmethod
    def stop_listener():
        """ Stops listener process (blocks).
        All bound processes won't crash, but their logs won't appear anymore (even after listener is restarted).
        Caller process will be unbound and returned to post-setup_root state. """
        if not Logger._LISTENER_ACTIVE:
            return
        Logger.get_logger("LOG_LISTENER").debug("Stopping...")
        Logger._LISTENER.stop()
        Logger._LISTENER.join()
        Logger._LISTENER_ACTIVE = False
        Logger.setup(Logger._CURRENT_CONFIG)
        Logger.get_logger("LOG_LISTENER").debug("Stopped")

    @staticmethod
    def clear_setup():
        """ Disables all configuration, this returns logging system to pre-setup_main state. """
        Logger.setup({})

    _CURRENT_CONFIG = {}
    _LISTENER = None
    _PIPE_HANDLER = None
    _LISTENER_ACTIVE = False

    @staticmethod
    def __serialize_setup__():
        return Logger._CURRENT_CONFIG, (Logger._PIPE_HANDLER if Logger._LISTENER_ACTIVE else None)

    @staticmethod
    def __deserialize_setup__(setup):
        config, pipe_handler = setup
        if pipe_handler:
            _config = deepcopy(config)
            _config.setdefault('root', {})
            _config['root']['handlers'] = []
            _config['root'].setdefault('level', 'DEBUG')
            Logger.setup(_config)
            Logger._CURRENT_CONFIG = config
            Logger._PIPE_HANDLER = pipe_handler
            logging.getLogger().addHandler(pipe_handler)
        else:
            Logger.setup(config)


@component
class LoggingComponent:
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        return Logger.get_logger(name)

    def sc_serialize(self):
        return Logger.__serialize_setup__()

    def sc_deserialize(self, setup):
        Logger.__deserialize_setup__(setup)


class _LogListenerProcess(WorkerProcess):
    def __init__(self):
        super().__init__(w_class=_LogListenerWorker, name="LoggerListener", daemon=False, ignore_sigterm=True)
        receiver, sender = multiprocessing.Pipe(duplex=False)
        pipe = sender
        _remote_pipe = receiver
        self.handler = _LogPipeHandler(pipe, _remote_pipe, multiprocessing.Lock())

    def start(self, config):
        super().start(config)

    def stop(self):
        self.handler.acquire()
        try:
            self.handler.pipe.send(None)
        finally:
            self.handler.release()


@component
class _LogListenerPipeComponent:
    def sc_serialize(self):
        return Logger._LISTENER.handler.pipe, Logger._LISTENER.handler._remote_pipe

    def sc_deserialize(self, pipes):
        self._remote_pipe, self.pipe = pipes


class _LogListenerWorker(_LogListenerPipeComponent, Worker):
    def run(self, config):
        Logger.setup(config)
        while True:
            record: logging.LogRecord = self.pipe.recv()
            if record is None:
                break
            if record.name == "root":
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(record.name)

            if logger.isEnabledFor(record.levelno):
                # The process name is transformed just to show that it's the listener
                # doing the logging to files and console
                # record.processName = '%s (for %s)' % (current_process().name, record.processName)
                logger.handle(record)
        logging.shutdown()


class _LogPipeHandler(logging.Handler):
    def __init__(self, pipe, _remote_pipe, lock):
        logging.Handler.__init__(self)
        self.pipe = pipe
        self._remote_pipe = _remote_pipe
        self.lock = lock

    def createLock(self) -> None:
        pass

    def emit(self, record):
        self.pipe.send(record)

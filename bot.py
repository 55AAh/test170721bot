import multiprocessing
import os
from types import GeneratorType

from server import Server
from db import Db
from telegram_api import TelegramApi
from logs import Logger


class Bot:
    def __init__(self):
        self.db = Db()
        self.tg_api = TelegramApi(os.getenv("TG_BOT_TOKEN"))
        self.server = Server(self)
        self.updates_handler = None
        self.current_promise = None
        self.logger = Logger()
        self.log = self.logger.get_logger("BOT")

    def run(self, updates_handler):
        self.updates_handler = updates_handler
        self.logger.setup()
        self.logger.start_listener()
        self.server.run()
        self.logger.stop_listener()

    def _continue_handling_tg_update(self, values=None):
        if self.current_promise:
            if values:
                generator = self.current_promise(*values)
            else:
                generator = self.current_promise._continue()
            yield next(generator)
            try:
                while True:
                    yield generator.send(self)
            except StopIteration as e:
                self.current_promise = None
                return e

    def _handle_tg_update(self, update):
        self.current_promise = self.get_promise()
        self.current_promise._actions = [self.updates_handler]
        yield from self._continue_handling_tg_update((update,))

    @staticmethod
    def get_promise():
        return Promise()


class Promise:
    def __init__(self):
        self._prev_promise = None
        self._prev_promise_results = []
        self._actions = []
        self._actions_results = []
        self._enable_interruption = True

    def then(self, *actions):
        self._actions = list(actions)
        new_promise = Promise()
        new_promise._enable_interruption = self._enable_interruption
        new_promise._prev_promise = self
        return new_promise

    def enable_interruption(self, enable):
        self._enable_interruption = enable
        return self

    def __call__(self, *values):
        if self._prev_promise:
            self._prev_promise_results = yield from self._prev_promise(*values)
            self._prev_promise = None
        else:
            self._prev_promise_results = values
        while self._actions:
            action = self._actions[0]
            if callable(action):
                if self._enable_interruption:
                    yield True
                action = action(*self._prev_promise_results)
                if isinstance(action, GeneratorType):
                    self._actions[0] = yield from action
                    continue
            del self._actions[0]
            if action is not None:
                self._actions_results.append(action)
        return tuple(self._actions_results)

    def _continue(self):
        return (yield from self(*self._prev_promise_results))


class _Promise:
    def __init__(self):
        self._actions = []
        self._last_result = []

    def then(self, *actions):
        self._actions.append(list(actions))
        return self

    def __call__(self, bot):
        while self._actions:
            actions = self._actions[0]
            next_result = []
            while actions:
                action_return_value = actions[0](*self._last_result)
                bot.tg_api.interruptable_action = False
                result = yield from bot._complete_action(action_return_value)
                del actions[0]
                next_result.append(result)
                yield
            del self._actions[0]
            self._last_result = next_result
        return self._last_result


if __name__ == 'bot':
    multiprocessing.set_start_method("spawn", force=True)

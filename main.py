from bot import Bot


class MainUpdateHandler:
    def __call__(self, update):
        bot = yield
        msg = update["message"]
        print("MAIN1")
        yield
        print("MAIN2")
        yield
        print("MAIN3")
        yield
        return bot.get_promise().then(
            bot.tg_api.echo_text(msg, "MAIN1"),
            bot.tg_api.echo_text(msg, "MAIN2"),
            bot.tg_api.echo_text(msg, "MAIN3"))\
            .then(ThenHandler1(msg))\
            .then("heh")\
            .then(ThenHandler3(msg))


class ThenHandler1:
    def __init__(self, msg):
        self.msg = msg

    def __call__(self, *_responses):
        bot = yield
        print("THEN1_1")
        yield
        print("THEN1_2")
        yield
        print("THEN1_3")
        yield
        return bot.get_promise().then(
            bot.tg_api.echo_text(self.msg, "THEN1_1"),
            bot.tg_api.echo_text(self.msg, "THEN1_2"),
            bot.tg_api.echo_text(self.msg, "THEN1_3"))\
            .then(ThenHandler2(self.msg))


class ThenHandler2:
    def __init__(self, msg):
        self.msg = msg

    def __call__(self, *_responses):
        bot = yield
        print("THEN2_1")
        yield
        print("THEN2_2")
        yield
        print("THEN2_3")
        yield
        return bot.get_promise().then(
            bot.tg_api.echo_text(self.msg, "THEN2_1"),
            bot.tg_api.echo_text(self.msg, "THEN2_2"),
            bot.tg_api.echo_text(self.msg, "THEN2_3"))


class ThenHandler3:
    def __init__(self, msg):
        self.msg = msg

    def __call__(self, *_responses):
        bot = yield
        print("THEN3_1")
        yield
        print("THEN3_2")
        yield
        print("THEN3_3")
        yield
        return bot.get_promise().then(
            bot.tg_api.echo_text(self.msg, "THEN3_1"),
            bot.tg_api.echo_text(self.msg, "THEN3_2"),
            bot.tg_api.echo_text(self.msg, "THEN3_3"))


def main():
    bot = Bot()
    bot.run(MainUpdateHandler())


if __name__ == '__main__':
    print("> APP STARTED <")
    main()
    print("> APP STOPPED <")

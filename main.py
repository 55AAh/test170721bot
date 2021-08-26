from bot import Bot


class MainUpdateHandler:
    def __call__(self, update):
        bot = yield
        bot.db.save_update(update)
        bot.log.info(f"UPDATE TEXT: {update.setdefault('message', {}).get('text')}")


def main():
    bot = Bot()
    bot.run(MainUpdateHandler())


if __name__ == '__main__':
    print("> APP STARTED <")
    main()
    print("> APP STOPPED <")

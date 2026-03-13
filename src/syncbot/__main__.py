from .bot import SyncBot


def main() -> None:
    bot = SyncBot()
    bot.run()


if __name__ == "__main__":
    main()

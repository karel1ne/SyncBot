from loguru import logger
from pyrogram.client import Client
from pyrogram.sync import idle

from .config import settings
from .handlers import register_handlers
from .logic import copy_message
from .state import state_manager
from .utils import setup_logging


class SyncBot:
    def __init__(self) -> None:
        self.app = Client(
            name=settings.SESSION_NAME,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            session_string=settings.SESSION_STRING,
        )

    async def sync_history(self) -> None:
        logger.info("Проверка истории сообщений...")
        last_id = state_manager.load_last_message_id()
        messages_to_copy = []

        history = self.app.get_chat_history(chat_id=settings.SOURCE_CHANNEL, limit=settings.HISTORY_LIMIT_INITIAL)
        if history:
            if last_id is None:
                logger.info(f"Первый запуск: собираем последние {settings.HISTORY_LIMIT_INITIAL} сообщений...")
                async for msg in history:
                    messages_to_copy.append(msg)
            else:
                logger.info(f"Поиск пропущенных сообщений после ID {last_id}...")
                # We reuse the history object or get a new one
                history2 = self.app.get_chat_history(
                    chat_id=settings.SOURCE_CHANNEL, limit=settings.HISTORY_LIMIT_CATCHUP
                )
                if history2:
                    async for msg in history2:
                        if msg.id <= last_id:
                            break
                        messages_to_copy.append(msg)
        if messages_to_copy:
            messages_to_copy.reverse()
            logger.info(f"Найдено {len(messages_to_copy)} сообщений для копирования.")
            for msg in messages_to_copy:
                await copy_message(self.app, msg)
        else:
            logger.info("Новых пропущенных сообщений нет.")

    async def start(self) -> None:
        setup_logging()
        logger.info("Запуск бота...")
        await self.app.start()

        await self.sync_history()

        register_handlers(self.app)
        logger.info(f"Слушаем новые сообщения из {settings.SOURCE_CHANNEL}...")

        await idle()
        await self.app.stop()

    def run(self) -> None:
        self.app.run(self.start())  # type: ignore

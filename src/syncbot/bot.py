import asyncio

from loguru import logger
from pyrogram import Client, idle

from .config import settings
from .handlers import register_handlers
from .logic import copy_message
from .state import state_manager
from .utils import setup_logging


class SyncBot:
    def __init__(self) -> None:
        self.app: Client = None  # type: ignore

    async def sync_history(self) -> None:
        logger.info("Checking message history...")
        last_id = state_manager.load_last_message_id()
        messages_to_copy = []

        history = self.app.get_chat_history(chat_id=settings.SOURCE_CHANNEL, limit=settings.HISTORY_LIMIT_INITIAL)
        if history:
            if last_id is None:
                logger.info(f"First run: collecting last {settings.HISTORY_LIMIT_INITIAL} messages...")
                async for msg in history:
                    messages_to_copy.append(msg)
            else:
                logger.info(f"Searching for missed messages after ID {last_id}...")
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
            logger.info(f"Found {len(messages_to_copy)} messages to copy.")
            for msg in messages_to_copy:
                await copy_message(self.app, msg)
        else:
            logger.info("No new missed messages found.")

    async def start(self) -> None:
        setup_logging()
        logger.info("Starting bot...")
        
        # Instantiate Client inside the loop
        self.app = Client(
            name=settings.SESSION_NAME,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            session_string=settings.SESSION_STRING,
        )

        async with self.app:
            await self.sync_history()
            register_handlers(self.app)
            logger.info(f"Listening for new messages from {settings.SOURCE_CHANNEL}...")
            await idle()

    def run(self) -> None:
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            pass

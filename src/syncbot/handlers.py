from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from .config import settings
from .logic import PROCESSED_GROUPS, copy_message
from .state import state_manager


async def process_new_message(client: Client, message: Message) -> None:
    if message.media_group_id and message.media_group_id in PROCESSED_GROUPS:
        return

    last_id = state_manager.load_last_message_id()
    if last_id and message.id <= last_id:
        return

    await copy_message(client, message)


def register_handlers(app: Client) -> None:
    app.add_handler(MessageHandler(process_new_message, filters=filters.chat(settings.SOURCE_CHANNEL)))

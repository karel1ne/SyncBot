import asyncio
import os
from pathlib import Path

from loguru import logger
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from sqlalchemy import select

from .config import settings
from .db import AsyncSessionLocal, MessageRecord, init_db
from .serializers import serialize_message
from .utils import setup_logging


class FetcherService:
    def __init__(self) -> None:
        self.app: Client = None  # type: ignore
        self.download_dir = Path(settings.DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def get_max_msg_id(self) -> int | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(MessageRecord.source_msg_id).order_by(MessageRecord.source_msg_id.desc()).limit(1)
            )
            return result.scalar_one_or_none()

    async def process_message(self, message: Message) -> None:
        # Ignore unsupported messages (like service messages if empty text and no media)
        if not message.text and not message.media:
            return

        msg_type, raw_content = serialize_message(message)
        
        # Determine status
        # Some media types don't need downloading (like poll, contact, location, venue, dice)
        needs_download = msg_type in (
            "photo", "video", "document", "audio", "voice", "video_note", "animation", "sticker"
        )
        status = "pending_download" if needs_download else "ready_to_publish"
        
        reply_to_msg_id = message.reply_to_message_id
        media_group_id = str(message.media_group_id) if message.media_group_id else None

        # Insert into DB
        async with AsyncSessionLocal() as session:
            # Check if exists (idempotency)
            existing = await session.execute(
                select(MessageRecord).where(MessageRecord.source_msg_id == message.id)
            )
            if existing.scalar_one_or_none():
                return  # Already processed

            record = MessageRecord(
                source_msg_id=message.id,
                media_group_id=media_group_id,
                reply_to_msg_id=reply_to_msg_id,
                message_type=msg_type,
                raw_content=raw_content,
                status=status,
            )
            session.add(record)
            await session.commit()
            
        logger.info(f"Saved message {message.id} to DB with status '{status}'")

        if needs_download:
            # We must await the download task to ensure we stop correctly if it fails
            # and to not overwhelm the system with parallel large downloads for history
            await self.download_media_task(message)

    async def download_media_task(self, message: Message) -> None:
        try:
            # Create a unique filename prefix just in case
            file_name_prefix = f"{message.id}_"
            download_path = self.download_dir / file_name_prefix
            
            logger.info(f"Downloading media for message {message.id}...")
            local_path = await message.download(file_name=str(download_path))
            
            if not local_path:
                raise Exception("Download returned None")
                
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MessageRecord).where(MessageRecord.source_msg_id == message.id)
                )
                record = result.scalar_one()
                record.local_media_path = str(local_path)
                record.status = "ready_to_publish"
                await session.commit()
                
            logger.info(f"Successfully downloaded media for message {message.id}")
            
        except Exception as e:
            error_msg = f"Failed to download media for message {message.id}: {e}"
            logger.error(error_msg)
            
            # Update DB with error
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MessageRecord).where(MessageRecord.source_msg_id == message.id)
                )
                record = result.scalar_one_or_none()
                if record:
                    record.status = "error"
                    record.error_text = error_msg
                    await session.commit()
            
            # Critical failure: Stop the fetcher to maintain strict order and prevent skipping
            logger.critical("Shutting down Fetcher due to download error!")
            os._exit(1)

    async def sync_history(self) -> None:
        logger.info("Checking message history...")
        last_id = await self.get_max_msg_id()
        messages_to_process = []

        history = self.app.get_chat_history(chat_id=settings.SOURCE_CHANNEL, limit=settings.HISTORY_LIMIT_INITIAL)
        if history:
            if last_id is None:
                logger.info(f"First run: collecting last {settings.HISTORY_LIMIT_INITIAL} messages...")
                async for msg in history:
                    messages_to_process.append(msg)
            else:
                logger.info(f"Searching for missed messages after ID {last_id}...")
                history2 = self.app.get_chat_history(
                    chat_id=settings.SOURCE_CHANNEL, limit=settings.HISTORY_LIMIT_CATCHUP
                )
                if history2:
                    async for msg in history2:
                        if msg.id <= last_id:
                            break
                        messages_to_process.append(msg)
                        
        if messages_to_process:
            messages_to_process.reverse()
            logger.info(f"Found {len(messages_to_process)} messages to process.")
            for msg in messages_to_process:
                await self.process_message(msg)
        else:
            logger.info("No new missed messages found.")

    async def start(self) -> None:
        setup_logging()
        logger.info("Initializing Database...")
        await init_db()
        
        logger.info("Starting Fetcher Service...")
        self.app = Client(
            name=settings.SESSION_NAME,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            session_string=settings.SESSION_STRING,
        )

        @self.app.on_message(filters.chat(settings.SOURCE_CHANNEL))
        async def on_new_message(client: Client, message: Message) -> None:
            await self.process_message(message)

        async with self.app:
            await self.sync_history()
            logger.info(f"Listening for new messages from {settings.SOURCE_CHANNEL}...")
            await idle()

    def run(self) -> None:
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("Fetcher stopped by user.")

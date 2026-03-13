import os
from typing import Any

from loguru import logger
from pyrogram import Client
from pyrogram.types import (
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from .config import settings
from .state import state_manager
from .utils import (
    observe,
    safe_sleep,
    timed_operation,
)

# Множество для отслеживания обработанных медиа-групп
PROCESSED_GROUPS: set[str] = set()


@observe("manual_group_copy")
async def manual_copy_group(client: Client, messages: list[Message]) -> bool:
    """Метод для обхода защиты от копирования для альбомов."""
    max_id = max(msg.id for msg in messages)
    file_paths = []
    try:
        media: list[Any] = []
        with timed_operation("manual_group_download", count=len(messages)):
            for i, msg in enumerate(messages):
                file_path = await msg.download()
                file_paths.append(file_path)

                caption = msg.caption or ""
                entities = msg.caption_entities or msg.entities

                if msg.photo:
                    media.append(
                        InputMediaPhoto(
                            file_path,
                            caption=caption if i == 0 else "",
                            caption_entities=entities if i == 0 else None,  # type: ignore
                        )
                    )
                elif msg.video:
                    media.append(
                        InputMediaVideo(
                            file_path,
                            caption=caption if i == 0 else "",
                            caption_entities=entities if i == 0 else None,  # type: ignore
                        )
                    )

        if media:
            await client.send_media_group(chat_id=settings.DEST_CHANNEL, media=media)

        for path in file_paths:
            if path and os.path.exists(path):
                os.remove(path)

        logger.info(f"✅ (Manual Group) Скопирован альбом. Max ID: {max_id}")
        state_manager.save_last_message_id(max_id)
        await safe_sleep()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при ручном копировании альбома: {e}")
        for path in file_paths:
            if path and os.path.exists(path):
                os.remove(path)
        return False


@observe("manual_single_copy")
async def manual_copy(client: Client, message: Message) -> bool:
    """Метод для обхода защиты от копирования: скачивает файл и загружает его заново."""
    try:
        file_path = None
        caption = message.caption or ""
        entities = message.caption_entities or message.entities

        if message.text:
            await client.send_message(chat_id=settings.DEST_CHANNEL, text=message.text, entities=entities)
        elif message.media:
            with timed_operation("manual_download"):
                file_path = await message.download()

            if message.photo:
                await client.send_photo(settings.DEST_CHANNEL, file_path, caption=caption, caption_entities=entities)
            elif message.video:
                await client.send_video(settings.DEST_CHANNEL, file_path, caption=caption, caption_entities=entities)
            elif message.document:
                await client.send_document(settings.DEST_CHANNEL, file_path, caption=caption, caption_entities=entities)
            elif message.animation:
                await client.send_animation(
                    settings.DEST_CHANNEL, file_path, caption=caption, caption_entities=entities
                )
            elif message.audio:
                await client.send_audio(settings.DEST_CHANNEL, file_path, caption=caption, caption_entities=entities)
            elif message.voice:
                await client.send_voice(settings.DEST_CHANNEL, file_path, caption=caption, caption_entities=entities)
            elif message.sticker and message.sticker.file_id:
                await client.send_sticker(settings.DEST_CHANNEL, message.sticker.file_id)
            else:
                logger.warning(f"⚠️ Тип медиа не поддерживается: {message.id}")
                return False

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        logger.info(f"✅ (Manual) Скопировано сообщение {message.id}")
        state_manager.save_last_message_id(message.id)
        await safe_sleep()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при ручном копировании {message.id}: {e}")
        if "file_path" in locals() and file_path and os.path.exists(file_path):
            os.remove(file_path)
        return False


async def copy_message(client: Client, message: Message) -> bool:
    # Использование contextualize позволяет автоматически добавить message_id во ВСЕ логи внутри блока,
    # включая те, что вызываются внутри вложенных функций (manual_copy и т.д.)
    with logger.contextualize(message_id=message.id, chat_id=settings.SOURCE_CHANNEL):
        try:
            if message.media_group_id:
                if message.media_group_id in PROCESSED_GROUPS:
                    return True

                logger.info(f"📦 Обнаружен альбом (ID группы: {message.media_group_id}), получаем все сообщения...")
                group_messages = await client.get_media_group(chat_id=settings.SOURCE_CHANNEL, message_id=message.id)

                try:
                    with timed_operation("copy_media_group"):
                        await client.copy_media_group(
                            chat_id=settings.DEST_CHANNEL,
                            from_chat_id=settings.SOURCE_CHANNEL,
                            message_id=message.id,
                        )
                    max_id = max(msg.id for msg in group_messages)
                    logger.info(f"✅ Альбом скопирован успешно. Max ID: {max_id}")
                    state_manager.save_last_message_id(max_id)
                    PROCESSED_GROUPS.add(message.media_group_id)
                    await safe_sleep()
                    return True
                except Exception as e:
                    if "CHAT_FORWARDS_RESTRICTED" in str(e):
                        logger.warning("⚠️ Альбом защищен, используем ручное копирование...")
                        success = await manual_copy_group(client, group_messages)
                        if success:
                            PROCESSED_GROUPS.add(message.media_group_id)
                        return success
                    raise e

            with timed_operation("copy_single_message"):
                await message.copy(chat_id=settings.DEST_CHANNEL)
            logger.info(f"✅ Скопировано сообщение {message.id}")
            state_manager.save_last_message_id(message.id)
            await safe_sleep()
            return True
        except Exception as e:
            if "CHAT_FORWARDS_RESTRICTED" in str(e):
                logger.warning(f"⚠️ Канал защищен, используем download/upload для {message.id}...")
                return await manual_copy(client, message)

            logger.error(f"❌ Ошибка копирования {message.id}: {e}")
            return False

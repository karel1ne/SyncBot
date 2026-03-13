import os
from typing import Any

from loguru import logger
from pyrogram.client import Client  # type: ignore
from pyrogram.errors import ChatForwardsRestricted
from pyrogram.types import (
    InputMediaAudio,
    InputMediaDocument,
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
                elif msg.audio:
                    media.append(
                        InputMediaAudio(
                            file_path,
                            caption=caption if i == 0 else "",
                            caption_entities=entities if i == 0 else None,  # type: ignore
                        )
                    )
                elif msg.document:
                    media.append(
                        InputMediaDocument(
                            file_path,
                            caption=caption if i == 0 else "",
                            caption_entities=entities if i == 0 else None,  # type: ignore
                        )
                    )

        if media:
            try:
                await client.send_media_group(chat_id=settings.DEST_CHANNEL, media=media)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при отправке альбома ({e}), отправляем медиа по одному...")
                for msg, path in zip(messages, file_paths):
                    await manual_copy(client, msg, file_path=path)


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
async def manual_copy(client: Client, message: Message, file_path: str | None = None) -> bool:
    """Метод для обхода защиты от копирования: скачивает файл и загружает его заново."""
    try:
        caption = message.caption or ""
        entities = message.caption_entities or message.entities

        if message.text:
            await client.send_message(chat_id=settings.DEST_CHANNEL, text=message.text, entities=entities)
        elif message.media:
            # Сначала обрабатываем типы, которые не требуют скачивания файла
            if message.poll:
                await client.send_poll(
                    chat_id=settings.DEST_CHANNEL,
                    question=message.poll.question,
                    options=[opt.text for opt in message.poll.options],
                    is_anonymous=message.poll.is_anonymous,
                    type=message.poll.type,
                    allows_multiple_answers=message.poll.allows_multiple_answers,
                    correct_option_id=message.poll.correct_option_id,
                    explanation=message.poll.explanation,
                    explanation_entities=message.poll.explanation_entities,
                    open_period=message.poll.open_period,
                    close_date=message.poll.close_date,
                    is_closed=message.poll.is_closed,
                )
            elif message.location:
                await client.send_location(
                    chat_id=settings.DEST_CHANNEL,
                    latitude=float(message.location.latitude),  # type: ignore
                    longitude=float(message.location.longitude),  # type: ignore
                )
            elif message.contact:
                await client.send_contact(
                    chat_id=settings.DEST_CHANNEL,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                    vcard=message.contact.vcard,
                )
            elif message.venue:
                await client.send_venue(
                    chat_id=settings.DEST_CHANNEL,
                    latitude=float(message.venue.location.latitude),  # type: ignore
                    longitude=float(message.venue.location.longitude),  # type: ignore
                    title=message.venue.title,
                    address=message.venue.address,
                    foursquare_id=message.venue.foursquare_id,
                    foursquare_type=message.venue.foursquare_type,
                )
            elif message.dice:
                await client.send_dice(chat_id=settings.DEST_CHANNEL, emoji=message.dice.emoji)
            else:
                # Если это скачиваемый тип, загружаем его (если еще не передан)
                if not file_path:
                    with timed_operation("manual_download"):
                        file_path = await message.download()

                if message.photo:
                    await client.send_photo(
                        settings.DEST_CHANNEL,
                        file_path,
                        caption=caption,
                        caption_entities=entities,  # type: ignore
                    )
                elif message.video:
                    await client.send_video(
                        settings.DEST_CHANNEL,
                        file_path,
                        caption=caption,
                        caption_entities=entities,  # type: ignore
                    )
                elif message.document:
                    await client.send_document(
                        settings.DEST_CHANNEL,
                        file_path,
                        caption=caption,
                        caption_entities=entities,  # type: ignore
                    )
                elif message.animation:
                    await client.send_animation(
                        settings.DEST_CHANNEL,
                        file_path,
                        caption=caption,
                        caption_entities=entities,  # type: ignore
                    )
                elif message.audio:
                    await client.send_audio(
                        settings.DEST_CHANNEL,
                        file_path,
                        caption=caption,
                        caption_entities=entities,  # type: ignore
                    )
                elif message.voice:
                    await client.send_voice(
                        settings.DEST_CHANNEL,
                        file_path,
                        caption=caption,
                        caption_entities=entities,  # type: ignore
                    )
                elif message.video_note:
                    await client.send_video_note(
                        settings.DEST_CHANNEL,
                        file_path,
                    )
                elif message.sticker:
                    await client.send_sticker(
                        settings.DEST_CHANNEL,
                        file_path,
                    )
                else:
                    # Определяем конкретные типы для информативного сообщения об ошибке
                    media_types = []
                    for attr in ["game", "invoice", "paid_media", "story", "giveaway", "giveaway_winners"]:
                        if getattr(message, attr, None):
                            media_types.append(attr)

                    type_info = f" ({', '.join(media_types)})" if media_types else f" ({message.media})"
                    logger.warning(f"⚠️ Тип медиа не поддерживается для ручного копирования: {message.id}{type_info}")
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
                group_id_str = str(message.media_group_id)
                if group_id_str in PROCESSED_GROUPS:
                    return True

                logger.info(f"📦 Обнаружен альбом (ID группы: {group_id_str}), получаем все сообщения...")
                group_messages = await client.get_media_group(chat_id=settings.SOURCE_CHANNEL, message_id=message.id)

                try:
                    with timed_operation("copy_media_group", expected_errors=(ChatForwardsRestricted,)):
                        await client.copy_media_group(
                            chat_id=settings.DEST_CHANNEL,
                            from_chat_id=settings.SOURCE_CHANNEL,
                            message_id=message.id,
                        )
                    max_id = max(msg.id for msg in group_messages)
                    logger.info(f"✅ Альбом скопирован успешно. Max ID: {max_id}")
                    state_manager.save_last_message_id(max_id)
                    PROCESSED_GROUPS.add(group_id_str)
                    await safe_sleep()
                    return True
                except Exception as e:
                    if isinstance(e, ChatForwardsRestricted) or "CHAT_FORWARDS_RESTRICTED" in str(e):
                        logger.warning("⚠️ Альбом защищен, используем ручное копирование...")
                        success = await manual_copy_group(client, group_messages)
                        if success:
                            PROCESSED_GROUPS.add(group_id_str)
                        return success
                    raise e

            with timed_operation("copy_single_message", expected_errors=(ChatForwardsRestricted,)):
                await message.copy(chat_id=settings.DEST_CHANNEL)
            logger.info(f"✅ Скопировано сообщение {message.id}")
            state_manager.save_last_message_id(message.id)
            await safe_sleep()
            return True
        except Exception as e:
            if isinstance(e, ChatForwardsRestricted) or "CHAT_FORWARDS_RESTRICTED" in str(e):
                logger.warning(f"⚠️ Канал защищен, используем download/upload для {message.id}...")
                return await manual_copy(client, message)

            logger.error(f"❌ Ошибка копирования {message.id}: {e}")
            return False

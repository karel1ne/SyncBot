import json
from typing import Any

from pyrogram.types import Message, MessageEntity


def serialize_entities(entities: list[MessageEntity] | None) -> list[dict[str, Any]] | None:
    if not entities:
        return None
    
    serialized = []
    for ent in entities:
        ent_dict = {
            "type": ent.type.name if hasattr(ent.type, "name") else str(ent.type),
            "offset": ent.offset,
            "length": ent.length,
        }
        if ent.url:
            ent_dict["url"] = ent.url
        if ent.user:
            ent_dict["user_id"] = ent.user.id
        if ent.language:
            ent_dict["language"] = ent.language
        if ent.custom_emoji_id:
            ent_dict["custom_emoji_id"] = str(ent.custom_emoji_id)
        serialized.append(ent_dict)
    
    return serialized


def serialize_message(message: Message) -> tuple[str, dict[str, Any]]:
    """
    Returns (message_type, raw_content_dict)
    """
    content: dict[str, Any] = {}
    msg_type = "unknown"

    if message.text:
        msg_type = "text"
        content["text"] = message.text
        content["entities"] = serialize_entities(message.entities)

    elif message.media:
        content["caption"] = message.caption or ""
        content["caption_entities"] = serialize_entities(message.caption_entities)

        if message.photo:
            msg_type = "photo"
        elif message.video:
            msg_type = "video"
        elif message.document:
            msg_type = "document"
        elif message.audio:
            msg_type = "audio"
        elif message.voice:
            msg_type = "voice"
        elif message.video_note:
            msg_type = "video_note"
        elif message.animation:
            msg_type = "animation"
        elif message.sticker:
            msg_type = "sticker"
        elif message.poll:
            msg_type = "poll"
            content["poll"] = {
                "question": message.poll.question,
                "options": [opt.text for opt in message.poll.options],
                "is_anonymous": message.poll.is_anonymous,
                "type": message.poll.type.name if hasattr(message.poll.type, "name") else str(message.poll.type),
                "allows_multiple_answers": message.poll.allows_multiple_answers,
                "correct_option_id": message.poll.correct_option_id,
                "explanation": message.poll.explanation,
                "explanation_entities": serialize_entities(message.poll.explanation_entities),
            }
        elif message.location:
            msg_type = "location"
            content["location"] = {
                "latitude": message.location.latitude,
                "longitude": message.location.longitude,
            }
        elif message.contact:
            msg_type = "contact"
            content["contact"] = {
                "phone_number": message.contact.phone_number,
                "first_name": message.contact.first_name,
                "last_name": message.contact.last_name,
                "vcard": message.contact.vcard,
            }
        elif message.venue:
            msg_type = "venue"
            content["venue"] = {
                "latitude": message.venue.location.latitude,
                "longitude": message.venue.location.longitude,
                "title": message.venue.title,
                "address": message.venue.address,
            }
        elif message.dice:
            msg_type = "dice"
            content["dice"] = {"emoji": message.dice.emoji}
        else:
            msg_type = "unsupported_media"
            
    return msg_type, content

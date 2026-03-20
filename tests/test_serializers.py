from unittest.mock import MagicMock

from pyrogram.enums import MessageEntityType, PollType
from pyrogram.types import Message, MessageEntity

from syncbot.serializers import serialize_entities, serialize_message


def test_serialize_entities():
    # Mock entities
    ent1 = MagicMock(spec=MessageEntity)
    ent1.type = MessageEntityType.BOLD
    ent1.offset = 0
    ent1.length = 5
    ent1.url = None
    ent1.user = None
    ent1.language = None
    ent1.custom_emoji_id = None

    ent2 = MagicMock(spec=MessageEntity)
    ent2.type = MessageEntityType.TEXT_LINK
    ent2.offset = 6
    ent2.length = 4
    ent2.url = "https://example.com"
    ent2.user = None
    ent2.language = None
    ent2.custom_emoji_id = None

    entities = [ent1, ent2]
    
    result = serialize_entities(entities)
    
    assert result is not None
    assert len(result) == 2
    assert result[0] == {"type": "BOLD", "offset": 0, "length": 5}
    assert result[1] == {"type": "TEXT_LINK", "offset": 6, "length": 4, "url": "https://example.com"}


def test_serialize_message_text():
    msg = MagicMock()
    msg.text = "Hello world"
    msg.media = None
    msg.entities = None
    
    msg_type, content = serialize_message(msg)
    
    assert msg_type == "text"
    assert content["text"] == "Hello world"
    assert content["entities"] is None


def test_serialize_message_photo():
    msg = MagicMock()
    msg.text = None
    msg.media = True
    msg.photo = True
    msg.video = None
    msg.caption = "Nice photo"
    msg.caption_entities = None
    
    msg_type, content = serialize_message(msg)
    
    assert msg_type == "photo"
    assert content["caption"] == "Nice photo"
    assert content["caption_entities"] is None


def test_serialize_message_poll():
    msg = MagicMock()
    msg.text = None
    msg.media = True
    msg.photo = None
    msg.video = None
    msg.document = None
    msg.audio = None
    msg.voice = None
    msg.video_note = None
    msg.animation = None
    msg.sticker = None
    msg.poll = MagicMock()
    msg.poll.question = "Yes or No?"
    
    opt1 = MagicMock()
    opt1.text = "Yes"
    opt2 = MagicMock()
    opt2.text = "No"
    
    msg.poll.options = [opt1, opt2]
    msg.poll.is_anonymous = True
    msg.poll.type = PollType.REGULAR
    msg.poll.allows_multiple_answers = False
    msg.poll.correct_option_id = None
    msg.poll.explanation = None
    msg.poll.explanation_entities = None
    
    msg.caption = None
    msg.caption_entities = None
    
    msg_type, content = serialize_message(msg)
    
    assert msg_type == "poll"
    assert content["poll"]["question"] == "Yes or No?"
    assert content["poll"]["options"] == ["Yes", "No"]
    assert content["poll"]["type"] == "REGULAR"

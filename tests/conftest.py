from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_safe_sleep():
    """Mock safe_sleep to avoid waiting during tests."""
    with patch("syncbot.logic.safe_sleep", AsyncMock()):
        yield

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mocks environment variables for the package."""
    monkeypatch.setenv("API_ID", "123456")
    monkeypatch.setenv("API_HASH", "mock_hash")
    monkeypatch.setenv("SOURCE_CHANNEL", "-100111111111")
    monkeypatch.setenv("DEST_CHANNEL", "-100222222222")

@pytest.fixture
def mock_app():
    """Mock Pyrogram Client."""
    client = MagicMock()
    client.start = AsyncMock()
    client.stop = AsyncMock()
    client.send_message = AsyncMock()
    client.send_photo = AsyncMock()
    client.send_video = AsyncMock()
    client.send_document = AsyncMock()
    client.send_animation = AsyncMock()
    client.send_audio = AsyncMock()
    client.send_voice = AsyncMock()
    client.send_sticker = AsyncMock()
    client.send_media_group = AsyncMock()
    client.get_media_group = AsyncMock()
    client.copy_media_group = AsyncMock()
    client.get_chat_history = MagicMock()
    return client

@pytest.fixture
def mock_message():
    """Mock Pyrogram Message."""
    message = MagicMock()
    message.id = 1
    message.media_group_id = None
    message.text = "Hello World"
    message.media = None
    message.caption = None
    message.entities = None
    message.caption_entities = None
    message.copy = AsyncMock()
    message.download = AsyncMock(return_value="temp_file.jpg")
    
    # Common media objects
    message.photo = None
    message.video = None
    message.document = None
    message.animation = None
    message.audio = None
    message.voice = None
    message.sticker = None
    
    return message

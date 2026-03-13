import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from syncbot.handlers import process_new_message
from syncbot.logic import PROCESSED_GROUPS, copy_message, manual_copy, manual_copy_group


@pytest.fixture(autouse=True)
def clear_processed_groups():
    """Clear the PROCESSED_GROUPS set before each test."""
    PROCESSED_GROUPS.clear()

@pytest.mark.asyncio
async def test_copy_message_single_success(mock_app, mock_message):
    """Test successful single message copy."""
    mock_message.media_group_id = None
    result = await copy_message(mock_app, mock_message)
    assert result is True
    mock_message.copy.assert_called_once()

@pytest.mark.asyncio
async def test_copy_message_restricted_fallback(mock_app, mock_message):
    """Test fallback to manual_copy when forwarding is restricted."""
    mock_message.copy.side_effect = Exception("CHAT_FORWARDS_RESTRICTED")
    
    with patch("syncbot.logic.manual_copy", AsyncMock(return_value=True)) as mock_manual:
        result = await copy_message(mock_app, mock_message)
        assert result is True
        mock_manual.assert_called_once_with(mock_app, mock_message)

@pytest.mark.asyncio
async def test_copy_message_media_group_success(mock_app, mock_message):
    """Test successful media group copy."""
    mock_message.media_group_id = "group123"
    
    msg2 = MagicMock()
    msg2.id = 2
    mock_app.get_media_group.return_value = [mock_message, msg2]
    
    result = await copy_message(mock_app, mock_message)
    assert result is True
    mock_app.copy_media_group.assert_called_once()
    assert "group123" in PROCESSED_GROUPS

@pytest.mark.asyncio
async def test_manual_copy_text(mock_app, mock_message):
    """Test manual copy of text message."""
    mock_message.text = "Hello"
    mock_message.media = None
    
    result = await manual_copy(mock_app, mock_message)
    assert result is True
    mock_app.send_message.assert_called_once()

@pytest.mark.parametrize("media_type", [
    "photo", "video", "document", "animation", "audio", "voice"
])
@pytest.mark.asyncio
async def test_manual_copy_media_types(mock_app, mock_message, tmp_path, media_type):
    """Test manual copy of various media types."""
    temp_file = tmp_path / f"test.{media_type}"
    temp_file.write_text("content")
    
    mock_message.text = None
    mock_message.media = True
    setattr(mock_message, media_type, MagicMock())
    mock_message.download.return_value = str(temp_file)
    
    result = await manual_copy(mock_app, mock_message)
    assert result is True
    send_method = getattr(mock_app, f"send_{media_type}")
    send_method.assert_called_once()
    assert not os.path.exists(str(temp_file))

@pytest.mark.asyncio
async def test_manual_copy_group(mock_app, tmp_path):
    """Test manual copy of a media group."""
    m1 = MagicMock(id=1, photo=MagicMock(), video=None, caption="C1", caption_entities=None)
    m2 = MagicMock(id=2, photo=None, video=MagicMock(), caption="C2", caption_entities=None)
    
    f1 = tmp_path / "1.jpg"
    f1.write_text("1")
    f2 = tmp_path / "2.mp4"
    f2.write_text("2")
    
    m1.download = AsyncMock(return_value=str(f1))
    m2.download = AsyncMock(return_value=str(f2))
    
    result = await manual_copy_group(mock_app, [m1, m2])
    assert result is True
    mock_app.send_media_group.assert_called_once()
    assert not os.path.exists(str(f1))
    assert not os.path.exists(str(f2))

@pytest.mark.asyncio
async def test_process_new_message_skip_processed(mock_app, mock_message):
    """Test that already processed groups are skipped."""
    mock_message.media_group_id = "already_done"
    PROCESSED_GROUPS.add("already_done")
    
    with patch("syncbot.handlers.copy_message", AsyncMock()) as mock_copy:
        await process_new_message(mock_app, mock_message)
        mock_copy.assert_not_called()

@pytest.mark.asyncio
async def test_process_new_message_skip_old_id(mock_app, mock_message):
    """Test that messages with ID <= last_message_id are skipped."""
    mock_message.id = 100
    
    with patch("syncbot.handlers.state_manager.load_last_message_id", return_value=150):
        with patch("syncbot.handlers.copy_message", AsyncMock()) as mock_copy:
            await process_new_message(mock_app, mock_message)
            mock_copy.assert_not_called()

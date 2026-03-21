import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from syncbot.db import AsyncSessionLocal, MessageRecord
from syncbot.fetcher import FetcherService


@pytest.mark.asyncio
async def test_process_message_text(mock_session):
    fetcher = FetcherService()
    
    msg = MagicMock()
    msg.id = 100
    msg.text = "Hello Test"
    msg.media = None
    msg.reply_to_message_id = None
    msg.media_group_id = None
    
    await fetcher.process_message(msg)
    
    # Verify DB insertion
    async with mock_session() as session:
        result = await session.execute(select(MessageRecord).where(MessageRecord.source_msg_id == 100))
        record = result.scalar_one_or_none()
        
        assert record is not None
        assert record.status == "ready_to_publish"
        assert record.message_type == "text"
        assert record.raw_content["text"] == "Hello Test"


@pytest.mark.asyncio
async def test_process_message_photo(mock_session):
    fetcher = FetcherService()
    
    msg = MagicMock()
    msg.id = 101
    msg.text = None
    msg.media = True
    msg.photo = True
    msg.video = None
    msg.caption = "Test Photo"
    msg.reply_to_message_id = None
    msg.media_group_id = None
    
    # Mock the download method
    msg.download = AsyncMock(return_value="/tmp/downloads/101_photo.jpg")
    
    await fetcher.process_message(msg)
    
    msg.download.assert_called_once()
    
    # Verify DB
    async with mock_session() as session:
        result = await session.execute(select(MessageRecord).where(MessageRecord.source_msg_id == 101))
        record = result.scalar_one_or_none()
        
        assert record is not None
        assert record.status == "ready_to_publish"  # Because download was successful
        assert record.message_type == "photo"
        assert record.local_media_path == "/tmp/downloads/101_photo.jpg"


@pytest.mark.asyncio
async def test_process_message_download_error(mock_session):
    fetcher = FetcherService()
    
    msg = MagicMock()
    msg.id = 102
    msg.text = None
    msg.media = True
    msg.photo = True
    msg.video = None
    msg.caption = "Test Error"
    msg.reply_to_message_id = None
    msg.media_group_id = None
    
    # Mock the download method to raise an exception
    msg.download = AsyncMock(side_effect=Exception("Network Timeout"))
    
    # Patch os._exit so the test doesn't actually stop
    with patch("os._exit") as mock_exit:
        await fetcher.process_message(msg)
        mock_exit.assert_called_once_with(1)
        
    # Verify DB
    async with mock_session() as session:
        result = await session.execute(select(MessageRecord).where(MessageRecord.source_msg_id == 102))
        record = result.scalar_one_or_none()
        
        assert record is not None
        assert record.status == "error"
        assert "Network Timeout" in record.error_text

import json

import pytest

from syncbot.config import Settings
from syncbot.state import StateManager


@pytest.mark.parametrize("val,expected", [
    ("-100123456789", -100123456789),
    ("12345", 12345),
    ("channel_name", "channel_name"),
    ("@my_channel", "@my_channel"),
])
def test_parse_channel_id(val, expected):
    """Test channel ID parsing in Settings."""
    # Settings validation logic
    assert Settings.parse_channel_id(val) == expected

def test_load_state_file_exists(tmp_path):
    """Test loading state when file exists."""
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"last_message_id": 12345}))
    
    manager = StateManager(str(state_file))
    assert manager.load_last_message_id() == 12345

def test_load_state_file_not_exists(tmp_path):
    """Test loading state when file does not exist."""
    state_file = tmp_path / "non_existent.json"
    manager = StateManager(str(state_file))
    assert manager.load_last_message_id() is None

def test_save_state(tmp_path):
    """Test saving state to a file."""
    state_file = tmp_path / "state.json"
    manager = StateManager(str(state_file))
    manager.save_last_message_id(54321)
    
    content = json.loads(state_file.read_text())
    assert content == {"last_message_id": 54321}

def test_load_state_invalid_json(tmp_path):
    """Test loading state with invalid JSON."""
    state_file = tmp_path / "state.json"
    state_file.write_text("invalid json")
    
    manager = StateManager(str(state_file))
    # StateManager handles JSONDecodeError by returning None and logging
    assert manager.load_last_message_id() is None

def test_timed_operation_unexpected_error(mocker):
    """Test timed_operation logs ERROR for standard exceptions."""
    from syncbot.utils import timed_operation
    mock_logger = mocker.patch("syncbot.utils.logger")
    
    with pytest.raises(ValueError, match="Test error"):
        with timed_operation("test_op"):
            raise ValueError("Test error")
            
    mock_logger.error.assert_called_once()
    assert "Operation test_op failed" in mock_logger.error.call_args[0][0]

def test_timed_operation_expected_error(mocker):
    """Test timed_operation logs DEBUG for expected exceptions."""
    from syncbot.utils import timed_operation
    mock_logger = mocker.patch("syncbot.utils.logger")
    
    class ExpectedError(Exception):
        pass

    with pytest.raises(ExpectedError, match="Test expected error"):
        with timed_operation("test_op", expected_errors=(ExpectedError,)):
            raise ExpectedError("Test expected error")
            
    mock_logger.error.assert_not_called()
    mock_logger.debug.assert_called_once()
    assert "Operation test_op failed with expected error ExpectedError" in mock_logger.debug.call_args[0][0]

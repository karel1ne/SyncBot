import json
import os

from loguru import logger

from .config import settings


class StateManager:
    def __init__(self, file_path: str = settings.STATE_FILE):
        self.file_path = file_path

    def load_last_message_id(self) -> int | None:
        log = logger.bind(state_file=self.file_path)
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path) as f:
                    data = json.load(f)
                    val = data.get("last_message_id")
                    return int(val) if val is not None else None
            except (json.JSONDecodeError, ValueError) as e:
                log.warning(f"Failed to load state: {e}")
        return None

    def save_last_message_id(self, msg_id: int) -> None:
        log = logger.bind(state_file=self.file_path, last_message_id=msg_id)
        try:
            with open(self.file_path, "w") as f:
                json.dump({"last_message_id": msg_id}, f)
        except Exception as e:
            log.error(f"Failed to save state: {e}")


state_manager = StateManager()

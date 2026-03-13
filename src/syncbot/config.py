from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_ID: int
    API_HASH: str
    SOURCE_CHANNEL: int | str
    DEST_CHANNEL: int | str

    # State file name
    STATE_FILE: str = "state.json"

    # Session name (used for .session file)
    SESSION_NAME: str = "my_account"

    # String session (optional, if using string instead of file)
    SESSION_STRING: str | None = None

    @field_validator("SOURCE_CHANNEL", "DEST_CHANNEL", mode="before")
    @classmethod
    def parse_channel_id(cls, v: int | str) -> int | str:
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return v
        return v


settings = Settings()  # type: ignore

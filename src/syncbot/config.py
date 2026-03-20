import os

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class Settings(BaseSettings):
    """
    Application settings.
    Secrets (API_ID, API_HASH, etc.) should be stored in .env.
    Other configuration parameters can be stored in config.yaml.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Secrets (Expected in .env) ---
    API_ID: int
    API_HASH: str
    SESSION_STRING: str | None = None
    PUBLISHER_BOT_TOKEN: str | None = None

    # --- Mode & Database ---
    MODE: str = "fetcher"  # fetcher or publisher
    DATABASE_URL: str = "sqlite+aiosqlite:///shared_data/syncbot.db"
    DOWNLOAD_DIR: str = "shared_data/downloads"

    # --- Configuration (Expected in config.yaml or .env) ---
    SOURCE_CHANNEL: int | str
    DEST_CHANNEL: int | str

    # Session name (used for .session file)
    SESSION_NAME: str = "my_account"

    # Syncbot parameters
    HISTORY_LIMIT_INITIAL: int = 100
    HISTORY_LIMIT_CATCHUP: int = 200
    SLEEP_DURATION: float = 2.0

    # Logging parameters
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "7 days"

    @field_validator("SOURCE_CHANNEL", "DEST_CHANNEL", mode="before")
    @classmethod
    def parse_channel_id(cls, v: int | str) -> int | str:
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return v
        return v

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
        **kwargs: object,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Priority order:
        1. Environment variables
        2. .env file
        3. config.yaml file
        4. Secrets
        """
        sources: list[PydanticBaseSettingsSource] = [init_settings, env_settings, dotenv_settings]
        if os.path.exists("config.yaml"):
            sources.append(YamlConfigSettingsSource(settings_cls, yaml_file="config.yaml", yaml_file_encoding="utf-8"))
        sources.append(file_secret_settings)
        return tuple(sources)


settings = Settings()  # type: ignore

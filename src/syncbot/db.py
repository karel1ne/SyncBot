from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings

# Ensure we use an async driver for sqlite
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite://") and not db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

# Initialize async engine
engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class MessageRecord(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_msg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    dest_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_group_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    reply_to_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    message_type: Mapped[str] = mapped_column(String, nullable=False)
    raw_content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    local_media_path: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Statuses: pending_download, ready_to_publish, publishing, published, error
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)
    error_text: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Using timezone.utc to be explicit, but defaults are usually local unless specified
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db() -> None:
    """Creates all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

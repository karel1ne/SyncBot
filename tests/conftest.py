import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
# Now we can import the rest

import pytest
from unittest.mock import AsyncMock, patch

from syncbot.db import AsyncSessionLocal, MessageRecord, Base, engine


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_session():
    return AsyncSessionLocal

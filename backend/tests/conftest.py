import asyncio
import pytest
import pytest_asyncio
import httpx
from backend.app.main import app
from backend.app.database.connection import init_db
from backend.app.queue.redis_client import close_redis, reset_redis_state
from backend.app.queue.stream_manager import stream_manager

@pytest_asyncio.fixture(autouse=True)
async def setup_test_environment():
    """Initializes DB schema and stream for every test, then cleanly tears down Redis connections."""
    await init_db()
    await stream_manager.init_stream()
    yield
    await close_redis()
    reset_redis_state()

@pytest_asyncio.fixture
async def async_client():
    """Provides an isolated AsyncClient for FastAPI endpoint testing."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.base import Base

# Import all models so Base.metadata is populated
import backend.app.models.event # noqa
import backend.app.models.worker # noqa
import backend.app.models.dlq # noqa

# Configure async engine
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30.0}
else:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db():
    logger.info("Initializing database tables...", extra={"database_url": settings.DATABASE_URL})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            try:
                res = await conn.exec_driver_sql("PRAGMA table_info(events)")
                cols = [row[1] for row in res.fetchall()]
                if cols and "next_retry_at" not in cols:
                    await conn.exec_driver_sql("ALTER TABLE events ADD COLUMN next_retry_at DATETIME")
            except Exception as e:
                logger.debug(f"SQLite schema migration check: {e}")
    logger.info("Database tables initialized successfully.")


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


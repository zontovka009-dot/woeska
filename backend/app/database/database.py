from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings, DEFAULT_DATABASE_URL


def _safe_database_url(value: str | None) -> str:
    """Use BotHost's persistent SQLite storage when DATABASE_URL is empty/invalid."""
    raw = str(value or "").strip()
    if not raw:
        return DEFAULT_DATABASE_URL

    # An accidental plain SQLite URL is fine; make it async.
    if raw.startswith("sqlite:///") and not raw.startswith("sqlite+aiosqlite:///"):
        raw = raw.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    # create_async_engine requires an async-capable dialect. If BotHost exposes
    # a placeholder/malformed value, do not let the whole web app crash.
    allowed = ("sqlite+aiosqlite://", "postgresql+asyncpg://")
    if not raw.startswith(allowed):
        return DEFAULT_DATABASE_URL

    return raw


DATABASE_URL = _safe_database_url(settings.database_url)

# Ensure BotHost's persistent SQLite directory exists.
if DATABASE_URL.startswith("sqlite+aiosqlite:////app/data/"):
    Path("/app/data").mkdir(parents=True, exist_ok=True)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

async def init_db():
    from app.models import user, session, friendship, message, invitation
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

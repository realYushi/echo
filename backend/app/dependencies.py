from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


_engine_cache: dict[str, async_sessionmaker[AsyncSession]] = {}


def _get_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create or return a cached async session factory."""
    if database_url not in _engine_cache:
        engine = create_async_engine(database_url, echo=False)
        _engine_cache[database_url] = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _engine_cache[database_url]


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session. One session per request."""
    factory = _get_session_factory(settings.database_url)
    async with factory() as session:
        yield session


async def get_qdrant_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncQdrantClient:
    """Return an async Qdrant client."""
    return AsyncQdrantClient(url=settings.qdrant_url)

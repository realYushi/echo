from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient


async def seed_catalog(
    qdrant_client: AsyncQdrantClient,
    collection: str,
) -> int:
    """Seed the product catalog into Qdrant. Returns number of products seeded."""
    raise NotImplementedError

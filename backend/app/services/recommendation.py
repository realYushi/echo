from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient

    from app.schemas.product import Recommendation


async def get_recommendations(
    persona_embedding: list[float],
    qdrant_client: AsyncQdrantClient,
    collection: str,
    limit: int = 10,
    score_threshold: float = 0.5,
) -> list[Recommendation]:
    """Retrieve product recommendations from Qdrant based on persona embedding."""
    raise NotImplementedError

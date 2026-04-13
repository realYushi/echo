from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.exceptions import ExternalServiceError
from app.schemas.product import Product, Recommendation

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient

logger = structlog.get_logger(__name__)


async def get_recommendations(
    persona_embedding: list[float],
    qdrant_client: AsyncQdrantClient,
    collection: str,
    limit: int = 10,
    score_threshold: float = 0.5,
) -> list[Recommendation]:
    """Retrieve product recommendations from Qdrant based on persona embedding."""
    try:
        response = await qdrant_client.query_points(
            collection_name=collection,
            query=persona_embedding,
            limit=limit,
            score_threshold=score_threshold,
        )
    except Exception as exc:
        await logger.aerror("qdrant_recommendation_search_failed", exc_info=exc)
        raise ExternalServiceError("qdrant", "Failed to search recommendations") from exc

    recommendations: list[Recommendation] = []
    for point in response.points:
        if point.payload is None:
            continue
        product = Product(**point.payload)
        recommendations.append(Recommendation(product=product, score=point.score))

    await logger.ainfo(
        "recommendations_retrieved",
        collection=collection,
        result_count=len(recommendations),
        limit=limit,
        score_threshold=score_threshold,
    )
    return recommendations

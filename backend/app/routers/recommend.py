from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient  # noqa: TC002 - FastAPI resolves annotations at runtime

from app.config import Settings  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.dependencies import get_qdrant_client, get_settings
from app.schemas.product import RecommendRequest  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.services.recommendation import get_recommendations
from app.services.session import get_session

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/recommend")
async def recommend(
    request: RecommendRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> list[dict[str, object]]:
    """Return product recommendations based on request or session persona embedding."""
    persona_embedding = request.persona_embedding
    if not persona_embedding:
        session = get_session(request.session_id)
        persona_embedding = session.get("persona_embedding", []) if session is not None else []

    if not persona_embedding:
        return []

    results = await get_recommendations(
        persona_embedding=persona_embedding,
        qdrant_client=qdrant_client,
        collection=settings.qdrant_collection,
        limit=settings.recommendation_limit,
        score_threshold=settings.recommendation_score_threshold,
    )

    await logger.ainfo(
        "recommend_endpoint_served",
        session_id=request.session_id,
        result_count=len(results),
    )
    return [r.model_dump(by_alias=True) for r in results]

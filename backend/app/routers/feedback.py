from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient  # noqa: TC002 - FastAPI resolves annotations at runtime

from app.config import Settings  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.dependencies import get_qdrant_client, get_settings
from app.exceptions import NotFoundError
from app.schemas.persona import Persona  # noqa: TC001 - used at runtime for Persona()
from app.schemas.product import FeedbackRequest  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.services.catalog import get_product
from app.services.persona import apply_feedback, embed_persona
from app.services.session import get_session, save_session

if TYPE_CHECKING:
    from app.agent.state import AgentState

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/feedback")
async def feedback(
    request: FeedbackRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> dict[str, object]:
    """Record user feedback on a product recommendation and return updated persona."""
    product = get_product(request.product_id)
    if product is None:
        raise NotFoundError(f"Product {request.product_id} not found")

    session = get_session(request.session_id)

    persona = session.get("persona") if session else None
    if persona is None:
        persona = Persona()

    updated_persona = apply_feedback(persona, product, request.signal)
    updated_embedding = await embed_persona(updated_persona)

    if session is not None:
        updated_state: AgentState = {
            **session,
            "persona": updated_persona,
            "persona_embedding": updated_embedding,
        }
        save_session(request.session_id, updated_state)

    await logger.ainfo(
        "feedback_recorded",
        session_id=request.session_id,
        product_id=request.product_id,
        signal=request.signal,
    )
    return {"persona": updated_persona.model_dump(by_alias=True)}

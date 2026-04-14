from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import structlog
from anthropic import AsyncAnthropic  # noqa: TC002 - FastAPI resolves annotations at runtime
from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient  # noqa: TC002 - FastAPI resolves annotations at runtime

from app.config import Settings  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.dependencies import get_anthropic_client, get_qdrant_client, get_settings
from app.schemas.voice import (  # noqa: TC001 - FastAPI resolves annotations at runtime
    TranscriptRequest,
    TranscriptResponse,
    VoiceTokenResponse,
)
from app.services.persona import (
    build_persona,
    embed_persona,
    persona_signal_count,
    post_process_messages,
)
from app.services.recommendation import get_recommendations
from app.services.session import get_session, save_session
from app.services.voice import create_ephemeral_token

if TYPE_CHECKING:
    from app.agent.state import AgentState

router = APIRouter(prefix="/voice", tags=["voice"])
logger = structlog.get_logger(__name__)


@router.post("/token")
async def voice_token(
    settings: Annotated[Settings, Depends(get_settings)],
) -> VoiceTokenResponse:
    """Generate a Gemini ephemeral token for Live API WebSocket connection."""
    token, model = await create_ephemeral_token(settings=settings)
    return VoiceTokenResponse(token=token, model=model)


@router.post("/transcript")
async def voice_transcript(
    request: TranscriptRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
    anthropic_client: Annotated[AsyncAnthropic | None, Depends(get_anthropic_client)],
) -> TranscriptResponse:
    """Process voice transcripts through the persona pipeline."""
    session_id = request.session_id

    session = get_session(session_id)
    existing_messages: list[dict[str, str]] = list(session.get("messages", [])) if session else []
    existing_persona = session.get("persona") if session else None

    new_messages = [{"role": m.role, "content": m.content} for m in request.messages]
    all_messages = [*existing_messages, *new_messages]

    post_process_result = await post_process_messages(
        all_messages,
        client=anthropic_client,
        model=settings.anthropic_post_process_model,
    )

    persona = existing_persona
    if post_process_result["has_new_signals"]:
        persona = await build_persona(
            post_process_result["filtered_signals"],
            existing_persona,
            client=anthropic_client,
            model=settings.anthropic_model,
        )

    persona_embedding: list[float] = []
    if persona is not None and persona_signal_count(persona) > 0:
        persona_embedding = await embed_persona(persona)

    recommendations = []
    if (
        persona is not None
        and persona_signal_count(persona) >= settings.min_recommendation_signals
        and persona_embedding
    ):
        recommendations = await get_recommendations(
            persona_embedding=persona_embedding,
            qdrant_client=qdrant_client,
            collection=settings.qdrant_collection,
            limit=settings.recommendation_limit,
            score_threshold=settings.recommendation_score_threshold,
        )

    updated_state: AgentState = {
        "session_id": session_id,
        "messages": all_messages,
        "persona": persona,
        "persona_embedding": persona_embedding,
        "recommendations": recommendations,
    }
    save_session(session_id, updated_state)

    await logger.ainfo(
        "voice_transcript_processed",
        session_id=session_id,
        new_message_count=len(new_messages),
        has_new_signals=post_process_result["has_new_signals"],
        recommendation_count=len(recommendations),
    )

    return TranscriptResponse(
        session_id=session_id,
        persona=persona,
        recommendations=recommendations,
    )

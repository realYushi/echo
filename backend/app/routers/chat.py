from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated

import structlog
from anthropic import AsyncAnthropic  # noqa: TC002 - FastAPI resolves annotations at runtime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from qdrant_client import AsyncQdrantClient  # noqa: TC002 - FastAPI resolves annotations at runtime

from app.agent.graph import run_agent_turn
from app.config import Settings  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.dependencies import get_anthropic_client, get_qdrant_client, get_settings
from app.schemas.chat import ChatRequest  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.services.session import get_session, save_session

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from app.agent.state import AgentState

router = APIRouter()
logger = structlog.get_logger(__name__)


def _sse_event(data: dict[str, object]) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _chat_stream(
    request: ChatRequest,
    settings: Settings,
    qdrant_client: AsyncQdrantClient,
    anthropic_client: AsyncAnthropic | None,
) -> AsyncGenerator[str, None]:
    session_id = request.session_id
    previous = get_session(session_id)

    messages: list[dict[str, str]] = list(previous.get("messages", [])) if previous else []
    messages.append({"role": "user", "content": request.message})

    state: AgentState = {
        "messages": messages,
        "session_id": session_id,
        "persona": previous.get("persona") if previous else None,
        "persona_embedding": previous.get("persona_embedding", []) if previous else [],
        "recommendations": previous.get("recommendations", []) if previous else [],
        "pending_feedback": None,
    }

    try:
        result = await run_agent_turn(
            state,
            settings=settings,
            qdrant_client=qdrant_client,
            anthropic_client=anthropic_client,
        )
    except Exception as exc:
        await logger.aerror("chat_agent_turn_failed", session_id=session_id, error=str(exc))
        yield _sse_event({"type": "error", "message": "Something went wrong. Please try again."})
        yield _sse_event({"type": "done"})
        return

    save_session(session_id, result)

    assistant_message = result.get("assistant_message", "")
    if assistant_message:
        yield _sse_event({"type": "token", "content": assistant_message})

    persona = result.get("persona")
    if persona is not None:
        yield _sse_event({"type": "persona_update", "persona": persona.model_dump(by_alias=True)})

    yield _sse_event({"type": "done"})

    await logger.ainfo("chat_turn_complete", session_id=session_id)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
    anthropic_client: Annotated[AsyncAnthropic | None, Depends(get_anthropic_client)],
) -> StreamingResponse:
    """Stream chat responses via SSE."""
    return StreamingResponse(
        _chat_stream(request, settings, qdrant_client, anthropic_client),
        media_type="text/event-stream",
    )

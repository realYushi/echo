from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from app.schemas.chat import ChatRequest

router = APIRouter()


async def _placeholder_stream() -> AsyncGenerator[str, None]:
    """Placeholder SSE stream."""
    yield 'data: {"message": "Chat endpoint stub -- not yet implemented"}\n\n'


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream chat responses via SSE. Stub implementation."""
    return StreamingResponse(
        _placeholder_stream(),
        media_type="text/event-stream",
    )

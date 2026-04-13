from __future__ import annotations

from app.schemas.base import CamelModel
from app.schemas.persona import Persona  # noqa: TC001 - Pydantic resolves field types at runtime


class ChatRequest(CamelModel):
    """Request body for the chat endpoint."""

    session_id: str
    message: str
    persona: Persona | None = None

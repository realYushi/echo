from __future__ import annotations

from typing import Literal

from app.schemas.base import CamelModel
from app.schemas.persona import Persona  # noqa: TC001 - Pydantic resolves field types at runtime
from app.schemas.product import Recommendation  # noqa: TC001 - Pydantic resolves field types at runtime

SessionMessageRole = Literal["user", "assistant"]


class SessionMessage(CamelModel):
    """Conversation message restored into the discovery workspace."""

    role: SessionMessageRole
    content: str


class SessionSnapshot(CamelModel):
    """Server-backed discovery state used to resume a session."""

    session_id: str
    messages: list[SessionMessage]
    persona: Persona | None = None
    recommendations: list[Recommendation]

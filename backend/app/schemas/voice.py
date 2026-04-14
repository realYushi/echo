from __future__ import annotations

from app.schemas.base import CamelModel
from app.schemas.persona import Persona  # noqa: TC001 - Pydantic resolves field types at runtime
from app.schemas.product import Recommendation  # noqa: TC001 - Pydantic resolves field types at runtime


class VoiceTokenResponse(CamelModel):
    """Ephemeral token for Gemini Live API WebSocket connection."""

    token: str
    model: str


class TranscriptMessage(CamelModel):
    """A single message from a voice conversation transcript."""

    role: str
    content: str


class TranscriptRequest(CamelModel):
    """Request body for voice transcript processing."""

    session_id: str
    messages: list[TranscriptMessage]


class TranscriptResponse(CamelModel):
    """Result of processing a voice transcript through the persona pipeline."""

    session_id: str
    persona: Persona | None = None
    recommendations: list[Recommendation] = []

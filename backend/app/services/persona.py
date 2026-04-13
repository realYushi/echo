from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic

    from app.schemas.persona import Persona


async def extract_persona(
    messages: list[dict[str, str]],
    client: AsyncAnthropic,
) -> Persona:
    """Extract persona from chat messages using Claude."""
    raise NotImplementedError


async def embed_persona(persona: Persona) -> list[float]:
    """Convert persona to embedding vector."""
    raise NotImplementedError

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from app.schemas.persona import Persona
    from app.schemas.product import Recommendation


class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    persona: Persona | None
    persona_embedding: list[float]
    recommendations: list[Recommendation]
    session_id: str

from __future__ import annotations

from typing import Literal, TypedDict

from app.schemas import persona as persona_schema  # noqa: TC001 - LangGraph resolves TypedDict annotations at runtime
from app.schemas import product as product_schema  # noqa: TC001 - LangGraph resolves TypedDict annotations at runtime


class PendingFeedback(TypedDict):
    product_id: str
    signal: Literal["like", "dislike"]


class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    persona: persona_schema.Persona | None
    persona_embedding: list[float]
    recommendations: list[product_schema.Recommendation]
    session_id: str
    assistant_message: str
    suggestions: list[str]
    pending_feedback: PendingFeedback | None
    has_new_signals: bool
    filtered_signals: str

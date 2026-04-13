from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.services.catalog import get_product
from app.services.persona import (
    apply_feedback,
    persona_signal_count,
)
from app.services.persona import (
    embed_persona as embed_persona_service,
)
from app.services.persona import (
    extract_persona as extract_persona_service,
)
from app.services.recommendation import get_recommendations

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from qdrant_client import AsyncQdrantClient

    from app.agent.state import AgentState
    from app.config import Settings
    from app.schemas.persona import Persona

logger = structlog.get_logger(__name__)

_GREETING = (
    "Hi — I can help narrow this down fast. What space are you working on, "
    "and what should I avoid showing you right away?"
)


def _assistant_count(messages: list[dict[str, str]]) -> int:
    return sum(1 for message in messages if message.get("role") == "assistant")


def _append_assistant_message(state: AgentState, content: str) -> AgentState:
    messages = [*state.get("messages", []), {"role": "assistant", "content": content}]
    return {
        **state,
        "messages": messages,
        "assistant_message": content,
    }


def _latest_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _fallback_discovery_reply(persona: Persona | None, latest_user_message: str) -> str:
    if persona is None or persona.project_type is None:
        return "Got it. Which part of the project should we focus on first — kitchen, bathroom, lighting, or furniture?"
    if not persona.style_preferences:
        return "Helpful. What look feels right to you — for example modern, warm, sculptural, or more minimalist?"
    if not persona.material_preferences:
        return "Which materials pull you in, and which ones are an immediate no?"
    if persona.budget_tier is None:
        return "Do you want me to stay mostly budget-conscious, mid-range, or premium/luxury?"
    if not persona.rejections:
        return "What would make you reject a product instantly so I can steer away from it?"
    if latest_user_message:
        snippet = latest_user_message[:40].rstrip()
        return f"Understood. Based on that, what should the next options feel more like than '{snippet}'?"
    return "I have enough to refine further. What should I lean into more on the next round?"


async def _claude_discovery_reply(
    messages: list[dict[str, str]],
    persona: Persona | None,
    client: AsyncAnthropic,
    model: str,
) -> str:
    prompt_parts = [
        "You are a concise interior product discovery assistant.",
        "Reply in 1-2 sentences.",
        "Acknowledge the user's latest signal.",
        "Ask exactly one next question that helps narrow recommendations.",
        "Focus on elimination-first discovery.",
    ]
    if persona is not None:
        prompt_parts.append(f"Current persona snapshot: {persona.model_dump_json()}")

    conversation = "\n".join(
        f"{message.get('role', 'unknown').upper()}: {message.get('content', '').strip()}"
        for message in messages
        if message.get("content")
    )

    response = await client.messages.create(
        model=model,
        max_tokens=180,
        system=" ".join(prompt_parts),
        messages=[{"role": "user", "content": conversation}],
    )

    text_parts: list[str] = []
    for block in getattr(response, "content", []):
        block_type = getattr(block, "type", None)
        block_text = getattr(block, "text", None)
        if block_type == "text" and isinstance(block_text, str):
            text_parts.append(block_text)
    return "".join(text_parts).strip()


async def greet(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    """Generate greeting and initial discovery questions."""
    messages = state.get("messages", [])
    if _assistant_count(messages) > 0:
        return state

    content = _GREETING
    if anthropic_client is not None:
        try:
            content = await _claude_discovery_reply(
                messages,
                state.get("persona"),
                anthropic_client,
                settings.anthropic_model,
            )
        except Exception as exc:
            await logger.awarn("agent_greet_fallback", session_id=state.get("session_id"), error=str(exc))

    await logger.ainfo("agent_greeted", session_id=state.get("session_id"))
    return _append_assistant_message(state, content)


async def discover(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    """Process user message in discovery conversation."""
    if state.get("assistant_message"):
        return state

    messages = state.get("messages", [])
    latest_user_message = _latest_user_message(messages)
    persona = state.get("persona")
    content = _fallback_discovery_reply(persona, latest_user_message)

    if anthropic_client is not None:
        try:
            content = await _claude_discovery_reply(messages, persona, anthropic_client, settings.anthropic_model)
        except Exception as exc:
            await logger.awarn("agent_discover_fallback", session_id=state.get("session_id"), error=str(exc))

    await logger.ainfo("agent_discovery_reply_generated", session_id=state.get("session_id"))
    return _append_assistant_message(state, content)


async def extract_persona(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    """Extract persona JSON from conversation."""
    persona = await extract_persona_service(
        state.get("messages", []),
        client=anthropic_client,
        model=settings.anthropic_model,
    )
    return {**state, "persona": persona}


async def embed_persona(state: AgentState) -> AgentState:
    """Convert persona to embedding vector."""
    persona = state.get("persona")
    if persona is None or persona_signal_count(persona) == 0:
        return {**state, "persona_embedding": []}

    embedding = await embed_persona_service(persona)
    return {**state, "persona_embedding": embedding}


async def recommend(
    state: AgentState,
    *,
    qdrant_client: AsyncQdrantClient,
    settings: Settings,
) -> AgentState:
    """Retrieve recommendations based on persona embedding."""
    persona = state.get("persona")
    persona_embedding = state.get("persona_embedding", [])
    if persona is None or persona_signal_count(persona) < settings.min_recommendation_signals or not persona_embedding:
        await logger.ainfo(
            "recommendations_skipped",
            session_id=state.get("session_id"),
            reason="insufficient_signals",
        )
        return {**state, "recommendations": []}

    recommendations = await get_recommendations(
        persona_embedding=persona_embedding,
        qdrant_client=qdrant_client,
        collection=settings.qdrant_collection,
        limit=settings.recommendation_limit,
        score_threshold=settings.recommendation_score_threshold,
    )
    return {**state, "recommendations": recommendations}


async def feedback(
    state: AgentState,
    *,
    qdrant_client: AsyncQdrantClient,
    settings: Settings,
) -> AgentState:
    """Process user feedback on recommendations."""
    pending_feedback = state.get("pending_feedback")
    if pending_feedback is None:
        return state

    product = get_product(pending_feedback["product_id"])
    if product is None:
        await logger.awarn(
            "feedback_product_missing",
            session_id=state.get("session_id"),
            product_id=pending_feedback["product_id"],
        )
        return {**state, "pending_feedback": None}

    persona = state.get("persona")
    if persona is None:
        from app.schemas.persona import Persona

        persona = Persona()

    updated_persona = apply_feedback(persona, product, pending_feedback["signal"])
    updated_embedding = await embed_persona_service(updated_persona)
    updated_recommendations = await get_recommendations(
        persona_embedding=updated_embedding,
        qdrant_client=qdrant_client,
        collection=settings.qdrant_collection,
        limit=settings.recommendation_limit,
        score_threshold=settings.recommendation_score_threshold,
    )

    await logger.ainfo(
        "feedback_applied",
        session_id=state.get("session_id"),
        product_id=product.id,
        signal=pending_feedback["signal"],
    )
    return {
        **state,
        "persona": updated_persona,
        "persona_embedding": updated_embedding,
        "recommendations": updated_recommendations,
        "pending_feedback": None,
    }

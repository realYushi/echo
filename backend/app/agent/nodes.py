from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog

from app.services.catalog import get_product
from app.services.persona import (
    anthropic_response_text,
    apply_feedback,
    build_anthropic_messages,
    extract_json_object,
    persona_signal_count,
    post_process_messages,
)
from app.services.persona import (
    build_persona as build_persona_service,
)
from app.services.persona import (
    embed_persona as embed_persona_service,
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

_DISCOVERY_SYSTEM_PROMPT = """
You are Echo, a warm and curious interior product discovery assistant.
Your job is to help the user build a taste profile for product recommendations.

Return JSON only with this shape:
{
  "reply": string,
  "suggestions": string[]
}

Rules:
- Keep `reply` to 1-2 short sentences.
- Sound genuinely interested, not scripted or robotic.
- Stay focused on discovering taste, materials, categories, budget, likes, and dislikes.
- If the user goes off-topic, briefly acknowledge it and gently steer back toward product discovery.
- Ask at most one forward-moving question.
- `suggestions` must contain 2-3 short quick replies the user could realistically tap next.
- Suggestions should be specific, natural, and helpful for preference discovery.
- Do not wrap the JSON in markdown fences.
""".strip()

_GREETING_ONLY_MESSAGES = {"hello", "hello!", "hey", "hey!", "hi", "hi!"}
_SMALL_TALK_PATTERNS = (
    "how are you",
    "how's it going",
    "hows it going",
    "what's up",
    "whats up",
)


def _assistant_count(messages: list[dict[str, str]]) -> int:
    return sum(1 for message in messages if message.get("role") == "assistant")


def _append_assistant_message(
    state: AgentState,
    content: str,
    suggestions: list[str] | None = None,
) -> AgentState:
    messages = [*state.get("messages", []), {"role": "assistant", "content": content}]
    return {
        **state,
        "messages": messages,
        "assistant_message": content,
        "suggestions": suggestions or [],
    }


def _latest_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(value.strip())
    return deduped


def _is_greeting_only(message: str) -> bool:
    normalized = " ".join(message.lower().split())
    return normalized in _GREETING_ONLY_MESSAGES


def _is_small_talk(message: str) -> bool:
    normalized = " ".join(message.lower().split())
    return any(pattern in normalized for pattern in _SMALL_TALK_PATTERNS)


def _merge_personas(base: Persona | None, overlay: Persona | None) -> Persona | None:
    if base is None and overlay is None:
        return None

    from app.schemas.persona import Persona

    merged = base.model_copy(deep=True) if base is not None else Persona()
    if overlay is None:
        return merged

    merged.budget_tier = overlay.budget_tier or merged.budget_tier
    merged.likes = _unique_preserve_order([*merged.likes, *overlay.likes])
    merged.hates = _unique_preserve_order([*merged.hates, *overlay.hates])
    merged.rejections = _unique_preserve_order([*merged.rejections, *overlay.rejections])
    merged.approvals = _unique_preserve_order([*merged.approvals, *overlay.approvals])
    return merged


def _fallback_suggestions(persona: Persona | None) -> list[str]:
    if persona is None or not persona.likes:
        return ["Kitchen refresh", "Bathroom redo", "Statement lighting"]
    if persona.budget_tier is None:
        return ["Keep it budget-aware", "Mid-range is fine", "Open to premium"]
    if not persona.hates and not persona.rejections:
        return ["Avoid glossy finishes", "Nothing too ornate", "Skip anything cold"]
    return ["Push it bolder", "Make it calmer", "Show more texture"]


def _fallback_discovery_reply(persona: Persona | None, latest_user_message: str) -> tuple[str, list[str]]:
    if persona is None or not persona.likes:
        if _is_small_talk(latest_user_message):
            return (
                "Doing well. What kind of products are you looking for today?",
                _fallback_suggestions(persona),
            )
        if _is_greeting_only(latest_user_message):
            return (
                "Hi. What kind of products are you looking for today?",
                _fallback_suggestions(persona),
            )
        return (
            "Got it. Tell me more about what you like and what to avoid.",
            _fallback_suggestions(persona),
        )
    if persona.budget_tier is None:
        return (
            "Do you want me to stay mostly budget-conscious, mid-range, or premium/luxury?",
            _fallback_suggestions(persona),
        )
    if not persona.hates and not persona.rejections:
        return (
            "What would make you reject a product instantly so I can steer away from it?",
            _fallback_suggestions(persona),
        )
    if latest_user_message:
        snippet = latest_user_message[:40].rstrip()
        return (
            f"Understood. Based on that, what should the next options feel more like than '{snippet}'?",
            _fallback_suggestions(persona),
        )
    return (
        "I have enough to refine further. What should I lean into more on the next round?",
        _fallback_suggestions(persona),
    )


def _parse_discovery_payload(raw_text: str) -> tuple[str, list[str]]:
    payload = extract_json_object(raw_text)
    reply = payload.get("reply")
    suggestions = payload.get("suggestions")

    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("Claude discovery payload is missing a reply")

    if not isinstance(suggestions, list):
        raise ValueError("Claude discovery payload is missing suggestions")

    cleaned_suggestions = [
        suggestion.strip() for suggestion in suggestions if isinstance(suggestion, str) and suggestion.strip()
    ]
    return reply.strip(), cleaned_suggestions[:3]


async def _claude_discovery_reply(
    messages: list[dict[str, str]],
    persona: Persona | None,
    client: AsyncAnthropic,
    model: str,
) -> tuple[str, list[str]]:
    prompt = _DISCOVERY_SYSTEM_PROMPT
    if persona is not None:
        prompt = f"{prompt}\n\nCurrent persona snapshot: {json.dumps(persona.model_dump())}"

    response = await client.messages.create(
        model=model,
        max_tokens=220,
        system=prompt,
        messages=build_anthropic_messages(messages),
    )
    return _parse_discovery_payload(anthropic_response_text(getattr(response, "content", [])))


async def greet(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    messages = state.get("messages", [])
    if _assistant_count(messages) > 0:
        return state

    latest_user_message = _latest_user_message(messages)
    persona = state.get("persona")
    content = _GREETING
    suggestions = _fallback_suggestions(persona)
    if anthropic_client is not None:
        try:
            content, suggestions = await _claude_discovery_reply(
                messages,
                persona,
                anthropic_client,
                settings.anthropic_model,
            )
        except Exception as exc:
            await logger.awarn("agent_greet_fallback", session_id=state.get("session_id"), error=str(exc))
            if latest_user_message and not _is_greeting_only(latest_user_message):
                content, suggestions = _fallback_discovery_reply(persona, latest_user_message)
    elif latest_user_message and not _is_greeting_only(latest_user_message):
        content, suggestions = _fallback_discovery_reply(persona, latest_user_message)

    await logger.ainfo("agent_greeted", session_id=state.get("session_id"))
    return _append_assistant_message(state, content, suggestions)


async def discover(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    if state.get("assistant_message"):
        return state

    messages = state.get("messages", [])
    latest_user_message = _latest_user_message(messages)
    persona = state.get("persona")
    content, suggestions = _fallback_discovery_reply(persona, latest_user_message)

    if anthropic_client is not None:
        try:
            content, suggestions = await _claude_discovery_reply(
                messages,
                persona,
                anthropic_client,
                settings.anthropic_model,
            )
        except Exception as exc:
            await logger.awarn("agent_discover_fallback", session_id=state.get("session_id"), error=str(exc))

    await logger.ainfo("agent_discovery_reply_generated", session_id=state.get("session_id"))
    return _append_assistant_message(state, content, suggestions)


async def post_process(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    result = await post_process_messages(
        state.get("messages", []),
        client=anthropic_client,
        model=settings.anthropic_post_process_model,
    )
    return {**state, "has_new_signals": result["has_new_signals"], "filtered_signals": result["filtered_signals"]}


async def build_persona(
    state: AgentState,
    *,
    anthropic_client: AsyncAnthropic | None,
    settings: Settings,
) -> AgentState:
    persona = await build_persona_service(
        state.get("filtered_signals", ""),
        state.get("persona"),
        client=anthropic_client,
        model=settings.anthropic_model,
    )
    return {**state, "persona": persona}


async def embed_persona(state: AgentState) -> AgentState:
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

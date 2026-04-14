from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, TypedDict, cast

import structlog

from app.utils.embeddings import get_clip_embedding

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from anthropic.types import MessageParam

    from app.schemas.persona import Persona
    from app.schemas.product import Product

logger = structlog.get_logger(__name__)

_POST_PROCESS_SYSTEM_PROMPT = """
You detect aesthetic taste signals in a home-design discovery chat.

Taste signals are reusable aesthetic preferences that apply across product types:
- Style/aesthetic preferences (modern, minimalist, warm, industrial, etc.)
- Material preferences (metal, wood, marble, leather, etc.)
- Color preferences (silver, matte black, warm tones, etc.)
- Texture/finish preferences (glossy, matte, brushed, etc.)
- Budget level hints (luxury, budget-friendly, no limit, etc.)
- Product approvals or rejections by name

NOT taste signals (ignore these):
- Functional requirements (size, dimensions, seating capacity, shape, quantity)
- Room-specific context (which room, project type)
- Personal details (family size, lifestyle)

Return JSON only:
{"has_new_signals": true/false, "filtered_signals": "concise summary of aesthetic taste signals only"}

If no taste signals exist, return {"has_new_signals": false, "filtered_signals": ""}.
""".strip()

_PERSONA_BUILDER_SYSTEM_PROMPT = (
    "You merge taste signals into a user persona for home-design product discovery.\n"
    "Return JSON only with these snake_case keys:\n"
    '- budget_tier: "budget" | "mid" | "premium" | null\n'
    "- likes: string[]\n"
    "- hates: string[]\n"
    "- approvals: string[]\n"
    "- rejections: string[]\n"
    "\n"
    "Rules:\n"
    '- `budget_tier` must be exactly one of: "budget", "mid", "premium", or null.\n'
    '  Map: "no limit"/"luxury"/"high-end" -> "premium"; '
    '"affordable"/"cheap" -> "budget"; "mid-range"/"moderate" -> "mid".\n'
    "- `likes` and `hates` are portable aesthetic taste descriptors: "
    "styles, materials, colors, textures, finishes.\n"
    "  NOT functional requirements (size, shape, capacity, room type).\n"
    "- Keep array values short, concrete, and deduplicated.\n"
    "- Merge new signals into the existing persona without losing prior entries.\n"
    "- `approvals` and `rejections` are specific product names the user approved or rejected."
)


class PostProcessResult(TypedDict):
    has_new_signals: bool
    filtered_signals: str


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        cleaned = value.strip()
        normalized = cleaned.lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped


def extract_json_object(raw_text: str) -> dict[str, object]:
    match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
    if match is None:
        raise ValueError("Claude response did not contain JSON")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("Claude response JSON was not an object")
    return payload


def anthropic_response_text(content_blocks: object) -> str:
    if not isinstance(content_blocks, list):
        return ""

    text_chunks: list[str] = []
    for block in content_blocks:
        block_type = getattr(block, "type", None)
        block_text = getattr(block, "text", None)
        if block_type == "text" and isinstance(block_text, str):
            text_chunks.append(block_text)
    return "".join(text_chunks).strip()


def build_anthropic_messages(messages: list[dict[str, str]]) -> list[MessageParam]:
    normalized_messages: list[MessageParam] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "").strip()
        if role not in {"user", "assistant"} or not content:
            continue

        if normalized_messages and normalized_messages[-1]["role"] == role:
            normalized_messages[-1]["content"] = f"{normalized_messages[-1]['content']}\n\n{content}"
            continue

        normalized_messages.append(cast("MessageParam", {"role": role, "content": content}))

    return normalized_messages


def _conversation_transcript(messages: list[dict[str, str]]) -> str:
    transcript_lines: list[str] = []
    for message in messages:
        role = message.get("role", "unknown").upper()
        content = message.get("content", "").strip()
        if content:
            transcript_lines.append(f"{role}: {content}")
    return "\n".join(transcript_lines)


async def post_process_messages(
    messages: list[dict[str, str]],
    *,
    client: AsyncAnthropic | None,
    model: str,
) -> PostProcessResult:
    fallback = PostProcessResult(has_new_signals=True, filtered_signals=_conversation_transcript(messages))

    if client is None:
        return fallback

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=200,
            system=_POST_PROCESS_SYSTEM_PROMPT,
            messages=build_anthropic_messages(messages)
            or [cast("MessageParam", {"role": "user", "content": _conversation_transcript(messages)})],
        )
    except Exception as exc:
        await logger.awarn("post_process_claude_failed", error=str(exc))
        return fallback

    raw_text = anthropic_response_text(getattr(response, "content", []))
    try:
        payload = extract_json_object(raw_text)
    except ValueError:
        await logger.awarn("post_process_parse_failed", raw_text=raw_text[:200])
        return fallback

    has_new_signals = bool(payload.get("has_new_signals", True))
    filtered_signals = str(payload.get("filtered_signals", ""))
    return PostProcessResult(has_new_signals=has_new_signals, filtered_signals=filtered_signals)


async def build_persona(
    filtered_signals: str,
    current_persona: Persona | None,
    *,
    client: AsyncAnthropic | None,
    model: str,
) -> Persona:
    from app.schemas.persona import Persona as PersonaModel

    fallback = current_persona if current_persona is not None else PersonaModel()

    if client is None:
        return fallback

    current_dump = current_persona.model_dump() if current_persona is not None else PersonaModel().model_dump()
    user_content = f"Current persona:\n{json.dumps(current_dump)}\n\nNew signals:\n{filtered_signals}"

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=400,
            system=_PERSONA_BUILDER_SYSTEM_PROMPT,
            messages=[cast("MessageParam", {"role": "user", "content": user_content})],
        )
    except Exception as exc:
        await logger.awarn("build_persona_claude_failed", error=str(exc))
        return fallback

    raw_text = anthropic_response_text(getattr(response, "content", []))
    try:
        payload = extract_json_object(raw_text)
        return PersonaModel.model_validate(payload)
    except (ValueError, Exception) as exc:
        await logger.awarn("build_persona_parse_failed", error=str(exc))
        return fallback


def persona_to_text(persona: Persona) -> str:
    fragments: list[str] = []
    if persona.likes:
        fragments.append(f"Taste likes: {', '.join(persona.likes)}.")
    if persona.hates:
        fragments.append(f"Taste dislikes: {', '.join(persona.hates)}.")
    if persona.budget_tier:
        fragments.append(f"Budget tier: {persona.budget_tier}.")
    if persona.approvals:
        fragments.append(f"Approved products: {', '.join(persona.approvals)}.")
    if persona.rejections:
        fragments.append(f"Rejected products: {', '.join(persona.rejections)}.")
    if not fragments:
        return "Early-stage home design discovery with no strong taste signals yet."
    return " ".join(fragments)


def persona_signal_count(persona: Persona) -> int:
    count = 0
    count += int(persona.budget_tier is not None)
    count += len(persona.likes)
    count += len(persona.hates)
    count += len(persona.approvals)
    count += len(persona.rejections)
    return count


def apply_feedback(persona: Persona, product: Product, signal: str) -> Persona:
    merged = persona.model_copy(deep=True)

    target = merged.approvals if signal == "like" else merged.rejections
    if product.name not in target:
        target.append(product.name)

    taste_target = merged.likes if signal == "like" else merged.hates
    for tag in product.tags:
        taste_target.append(tag)
    taste_target.append(product.name)

    merged.likes = _unique_preserve_order(merged.likes)
    merged.hates = _unique_preserve_order(merged.hates)
    merged.approvals = _unique_preserve_order(merged.approvals)
    merged.rejections = _unique_preserve_order(merged.rejections)
    return merged


async def embed_persona(persona: Persona) -> list[float]:
    return await get_clip_embedding(persona_to_text(persona))

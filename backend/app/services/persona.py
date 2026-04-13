from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import structlog

from app.schemas.product import Product
from app.utils.embeddings import get_clip_embedding

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic

    from app.schemas.persona import Persona
    from app.schemas.product import Product

logger = structlog.get_logger(__name__)

_PROJECT_KEYWORDS: dict[str, str] = {
    "bathroom": "bathroom",
    "ensuite": "bathroom",
    "foyer": "entryway",
    "hallway": "hallway",
    "home": "whole-home",
    "kitchen": "kitchen",
    "lighting": "lighting",
    "living room": "living-room",
    "lounge": "living-room",
    "outdoor": "outdoor",
    "patio": "outdoor",
}

_ROLE_KEYWORDS: dict[str, str] = {
    "architect": "architect",
    "builder": "builder",
    "client": "designer",
    "contractor": "builder",
    "designer": "designer",
    "family": "homeowner",
    "homeowner": "homeowner",
    "renovating": "homeowner",
}

_BUDGET_KEYWORDS: dict[str, str] = {
    "affordable": "budget",
    "bespoke": "premium",
    "budget": "budget",
    "high-end": "premium",
    "luxury": "premium",
    "mid-range": "mid",
    "premium": "premium",
}

_STYLE_KEYWORDS: tuple[str, ...] = (
    "ambient",
    "art-deco",
    "bold",
    "gallery",
    "geometric",
    "industrial",
    "luxury",
    "mid-century",
    "minimalist",
    "modern",
    "organic",
    "rustic",
    "scandinavian",
    "sculptural",
    "spa",
    "warm",
)

_MATERIAL_KEYWORDS: tuple[str, ...] = (
    "brass",
    "chrome",
    "concrete",
    "glass",
    "leather",
    "linen",
    "marble",
    "nickel",
    "oak",
    "quartz",
    "quartzite",
    "steel",
    "stone",
    "tile",
    "velvet",
    "walnut",
    "wood",
)

_CATEGORY_KEYWORDS: tuple[str, ...] = (
    "bathroom",
    "furniture",
    "hardware",
    "kitchen",
    "lighting",
    "living-room",
    "outdoor",
    "storage",
)

_POSITIVE_CUES: tuple[str, ...] = ("like", "love", "prefer", "want", "drawn to")
_NEGATIVE_CUES: tuple[str, ...] = ("avoid", "don't", "do not", "hate", "not for me", "too ", "won't")

_PERSONA_SYSTEM_PROMPT = """
You extract a structured home-design preference persona from a discovery chat.
Return JSON only with these snake_case keys:
- project_type: string | null
- budget_tier: string | null
- role: string | null
- style_preferences: string[]
- material_preferences: string[]
- categories: string[]
- rejections: string[]
- approvals: string[]

Rules:
- Use null for unknown scalar fields.
- Keep array values short, concrete, and deduplicated.
- Prioritize explicit user statements over inference.
- Capture dislikes in rejections and likes in approvals.
""".strip()


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


def _extract_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def _extract_first_mapping(text: str, mapping: dict[str, str]) -> str | None:
    for keyword, value in mapping.items():
        if keyword in text:
            return value
    return None


def _extract_cued_phrases(messages: list[dict[str, str]], cues: tuple[str, ...]) -> list[str]:
    phrases: list[str] = []
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content", "").strip()
        lowered = content.lower()
        if any(cue in lowered for cue in cues):
            phrases.append(content[:120])
    return _unique_preserve_order(phrases)


def _extract_json_object(raw_text: str) -> dict[str, object]:
    match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
    if match is None:
        raise ValueError("Claude response did not contain JSON")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("Claude response JSON was not an object")
    return payload


def _response_text(content_blocks: object) -> str:
    if not isinstance(content_blocks, list):
        return ""

    text_chunks: list[str] = []
    for block in content_blocks:
        block_type = getattr(block, "type", None)
        block_text = getattr(block, "text", None)
        if block_type == "text" and isinstance(block_text, str):
            text_chunks.append(block_text)
    return "".join(text_chunks).strip()


def _conversation_transcript(messages: list[dict[str, str]]) -> str:
    transcript_lines: list[str] = []
    for message in messages:
        role = message.get("role", "unknown").upper()
        content = message.get("content", "").strip()
        if content:
            transcript_lines.append(f"{role}: {content}")
    return "\n".join(transcript_lines)


def _heuristic_persona(messages: list[dict[str, str]]) -> Persona:
    from app.schemas.persona import Persona

    user_text = " ".join(
        message.get("content", "")
        for message in messages
        if message.get("role") == "user"
    ).lower()

    persona = Persona(
        project_type=_extract_first_mapping(user_text, _PROJECT_KEYWORDS),
        budget_tier=_extract_first_mapping(user_text, _BUDGET_KEYWORDS),
        role=_extract_first_mapping(user_text, _ROLE_KEYWORDS),
        style_preferences=_unique_preserve_order(_extract_keywords(user_text, _STYLE_KEYWORDS)),
        material_preferences=_unique_preserve_order(_extract_keywords(user_text, _MATERIAL_KEYWORDS)),
        categories=_unique_preserve_order(_extract_keywords(user_text, _CATEGORY_KEYWORDS)),
        rejections=_extract_cued_phrases(messages, _NEGATIVE_CUES),
        approvals=_extract_cued_phrases(messages, _POSITIVE_CUES),
    )

    if persona.project_type and persona.project_type not in persona.categories:
        persona.categories.append(persona.project_type)
    persona.categories = _unique_preserve_order(persona.categories)
    return persona


async def _extract_persona_with_claude(
    messages: list[dict[str, str]],
    client: AsyncAnthropic,
    model: str,
) -> Persona:
    from app.exceptions import ExternalServiceError
    from app.schemas.persona import Persona

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=400,
            system=_PERSONA_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": _conversation_transcript(messages),
                }
            ],
        )
    except Exception as exc:
        raise ExternalServiceError("claude", "Failed to extract persona") from exc

    raw_text = _response_text(getattr(response, "content", []))
    payload = _extract_json_object(raw_text)
    return Persona.model_validate(payload)


def persona_to_text(persona: Persona) -> str:
    """Render persona into a compact embedding prompt."""
    fragments: list[str] = []

    if persona.project_type:
        fragments.append(f"Project type: {persona.project_type}.")
    if persona.role:
        fragments.append(f"Customer role: {persona.role}.")
    if persona.budget_tier:
        fragments.append(f"Budget tier: {persona.budget_tier}.")
    if persona.categories:
        fragments.append(f"Interested categories: {', '.join(persona.categories)}.")
    if persona.style_preferences:
        fragments.append(f"Preferred styles: {', '.join(persona.style_preferences)}.")
    if persona.material_preferences:
        fragments.append(f"Preferred materials: {', '.join(persona.material_preferences)}.")
    if persona.approvals:
        fragments.append(f"Positive signals: {', '.join(persona.approvals)}.")
    if persona.rejections:
        fragments.append(f"Avoid: {', '.join(persona.rejections)}.")

    if not fragments:
        return "Early-stage home design discovery with no strong taste signals yet."
    return " ".join(fragments)


def persona_signal_count(persona: Persona) -> int:
    """Return the number of distinct persona signals captured so far."""
    count = 0
    count += int(persona.project_type is not None)
    count += int(persona.budget_tier is not None)
    count += int(persona.role is not None)
    count += len(_unique_preserve_order(persona.style_preferences))
    count += len(_unique_preserve_order(persona.material_preferences))
    count += len(_unique_preserve_order(persona.categories))
    count += len(_unique_preserve_order(persona.rejections))
    count += len(_unique_preserve_order(persona.approvals))
    return count


def apply_feedback(persona: Persona, product: Product, signal: str) -> Persona:
    """Merge recommendation feedback into the persona."""
    merged = persona.model_copy(deep=True)

    if product.category not in merged.categories:
        merged.categories.append(product.category)

    style_hits = [tag for tag in product.tags if tag in _STYLE_KEYWORDS]
    material_hits = [tag for tag in product.tags if tag in _MATERIAL_KEYWORDS]

    for style in style_hits:
        if style not in merged.style_preferences:
            merged.style_preferences.append(style)
    for material in material_hits:
        if material not in merged.material_preferences:
            merged.material_preferences.append(material)

    target = merged.approvals if signal == "like" else merged.rejections
    if product.name not in target:
        target.append(product.name)

    merged.categories = _unique_preserve_order(merged.categories)
    merged.style_preferences = _unique_preserve_order(merged.style_preferences)
    merged.material_preferences = _unique_preserve_order(merged.material_preferences)
    merged.approvals = _unique_preserve_order(merged.approvals)
    merged.rejections = _unique_preserve_order(merged.rejections)
    return merged


async def extract_persona(
    messages: list[dict[str, str]],
    client: AsyncAnthropic | None,
    model: str | None = None,
) -> Persona:
    """Extract persona from chat messages using Claude, with heuristic fallback."""
    if not messages:
        from app.schemas.persona import Persona

        return Persona()

    heuristic = _heuristic_persona(messages)
    if client is None or not model:
        await logger.ainfo("persona_extraction_fallback", reason="anthropic_not_configured")
        return heuristic

    try:
        persona = await _extract_persona_with_claude(messages, client, model)
    except Exception as exc:
        await logger.awarn("persona_extraction_fallback", reason="claude_failed", error=str(exc))
        return heuristic

    await logger.adebug(
        "persona_extracted",
        project_type=persona.project_type,
        signal_count=persona_signal_count(persona),
    )
    return persona


async def embed_persona(persona: Persona) -> list[float]:
    """Convert persona to embedding vector."""
    return await get_clip_embedding(persona_to_text(persona))

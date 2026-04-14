from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, cast

import structlog

from app.utils.embeddings import get_clip_embedding

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from anthropic.types import MessageParam

    from app.schemas.persona import Persona
    from app.schemas.product import Product

logger = structlog.get_logger(__name__)

_PROJECT_KEYWORDS: dict[str, str] = {
    "bathroom": "bathroom",
    "bedroom": "bedroom",
    "dining room": "dining-room",
    "dining": "dining-room",
    "ensuite": "bathroom",
    "foyer": "entryway",
    "hallway": "hallway",
    "home": "whole-home",
    "kitchen": "kitchen",
    "lighting": "lighting",
    "living room": "living-room",
    "lounge": "living-room",
    "nursery": "nursery",
    "office": "office",
    "outdoor": "outdoor",
    "patio": "outdoor",
    "study": "office",
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
    "bohemian",
    "bold",
    "classic",
    "coastal",
    "contemporary",
    "eclectic",
    "farmhouse",
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
    "traditional",
    "transitional",
    "warm",
)

_MATERIAL_KEYWORDS: tuple[str, ...] = (
    "brass",
    "ceramic",
    "chrome",
    "concrete",
    "copper",
    "cotton",
    "fabric",
    "glass",
    "leather",
    "linen",
    "marble",
    "metal",
    "nickel",
    "oak",
    "plastic",
    "porcelain",
    "quartz",
    "quartzite",
    "rattan",
    "steel",
    "stone",
    "tile",
    "upholstered",
    "velvet",
    "walnut",
    "wood",
    "wool",
)

_ALLOWED_CATEGORIES: tuple[str, ...] = (
    "furniture",
    "bathroom",
    "kitchen",
    "lighting",
    "building-materials",
)

_CATEGORY_KEYWORDS: dict[str, str] = {
    "armchair": "furniture",
    "bar stool": "furniture",
    "bathroom": "bathroom",
    "bathtub": "bathroom",
    "bed": "furniture",
    "bench": "furniture",
    "bookcase": "furniture",
    "cabinet": "furniture",
    "chair": "furniture",
    "countertop": "building-materials",
    "desk": "furniture",
    "dresser": "furniture",
    "flooring": "building-materials",
    "furniture": "furniture",
    "kitchen": "kitchen",
    "lamp": "lighting",
    "lighting": "lighting",
    "mirror": "bathroom",
    "oak flooring": "building-materials",
    "ottoman": "furniture",
    "pendant": "lighting",
    "shelf": "furniture",
    "shelving": "furniture",
    "shower": "bathroom",
    "slab": "building-materials",
    "sofa": "furniture",
    "stool": "furniture",
    "stone": "building-materials",
    "table": "furniture",
    "tile": "building-materials",
    "vanity": "bathroom",
}

_POSITIVE_CUES: tuple[str, ...] = ("like", "love", "prefer", "want", "drawn to")
_NEGATIVE_CUES: tuple[str, ...] = ("avoid", "don't", "do not", "hate", "not for me", "too ", "won't")
_COLOR_KEYWORDS: tuple[str, ...] = (
    "beige",
    "black",
    "blue",
    "brown",
    "cream",
    "gold",
    "green",
    "grey",
    "gray",
    "navy",
    "orange",
    "pink",
    "purple",
    "red",
    "teal",
    "terracotta",
    "white",
    "yellow",
)
_NEGATION_MARKERS: tuple[str, ...] = ("don't", "don'", "do not", "never", "not", "no")
_FILLER_AFTER_CUE = re.compile(
    r"^((like|want|need|prefer|have|any|a|an|the|following|to|for|some|it|that)\b\s*)+",
    re.IGNORECASE,
)
_SEGMENT_SPLIT_RE = re.compile(r"[,;:]+|\.\s+|\n+|\d+\.\s*|\s{2,}")
_CUE_CONTEXT_RANGE = 4

_PERSONA_SYSTEM_PROMPT = """
You extract a structured home-design preference persona from a discovery chat.
Return JSON only with these snake_case keys:
- project_type: string | null
- budget_tier: string | null
- role: string | null
- likes: string[]
- hates: string[]
- style_preferences: string[]
- material_preferences: string[]
- categories: string[]
- rejections: string[]
- approvals: string[]

Rules:
- Use null for unknown scalar fields.
- Keep array values short, concrete, and deduplicated.
- Prioritize explicit user statements over inference.
- `likes` and `hates` should be compact taste descriptors, not full sentences.
- Map categories only to this fixed allowlist: furniture, bathroom, kitchen, lighting, building-materials.
- Capture specific dislikes in rejections and specific likes in approvals.
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


def _extract_mapped_keywords(text: str, mapping: dict[str, str]) -> list[str]:
    hits: list[str] = []
    for keyword, value in mapping.items():
        if keyword in text:
            hits.append(value)
    return _unique_preserve_order(hits)


def _extract_first_mapping(text: str, mapping: dict[str, str]) -> str | None:
    for keyword, value in mapping.items():
        if keyword in text:
            return value
    return None


def _split_segments(text: str) -> list[str]:
    return [s.strip() for s in _SEGMENT_SPLIT_RE.split(text) if s.strip()]


def _is_negated(text: str, cue_start: int) -> bool:
    prefix = text[:cue_start].rstrip()
    return any(prefix.endswith(marker) for marker in _NEGATION_MARKERS)


_MAX_CUE_PHRASE_LEN = 30


def _extract_cued_phrases(
    messages: list[dict[str, str]],
    cues: tuple[str, ...],
    *,
    skip_if_negated: bool = False,
) -> list[str]:
    phrases: list[str] = []
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content", "").strip()
        for segment in _split_segments(content):
            lowered = segment.lower()
            for cue in cues:
                idx = lowered.find(cue)
                if idx == -1:
                    continue
                if skip_if_negated and _is_negated(lowered, idx):
                    continue
                after = segment[idx + len(cue) :].strip()
                after = _FILLER_AFTER_CUE.sub("", after).strip()
                if after and 1 < len(after) <= _MAX_CUE_PHRASE_LEN:
                    phrases.append(after)
                break
    return _unique_preserve_order(phrases)


def _extract_cued_keyword_hits(
    messages: list[dict[str, str]],
    cues: tuple[str, ...],
    keywords: tuple[str, ...],
    *,
    opposing_cues: tuple[str, ...] = (),
    skip_if_negated: bool = False,
) -> list[str]:
    hits: list[str] = []
    for message in messages:
        if message.get("role") != "user":
            continue
        segments = _split_segments(message.get("content", ""))
        cue_active_until = -1
        for i, segment in enumerate(segments):
            lowered = segment.lower()
            if opposing_cues and any(c in lowered for c in opposing_cues):
                cue_active_until = -1
            has_cue = False
            for cue in cues:
                idx = lowered.find(cue)
                if idx == -1:
                    continue
                if skip_if_negated and _is_negated(lowered, idx):
                    continue
                has_cue = True
                break
            if has_cue:
                cue_active_until = i + _CUE_CONTEXT_RANGE - 1
            if i <= cue_active_until:
                hits.extend(keyword for keyword in keywords if keyword in lowered)
    return _unique_preserve_order(hits)


def _derive_taste_descriptors(
    *,
    categories: list[str],
    styles: list[str],
    materials: list[str],
    approvals: list[str],
    rejections: list[str],
) -> tuple[list[str], list[str]]:
    likes = _unique_preserve_order(
        [
            *styles,
            *materials,
            *approvals,
        ]
    )
    hates = _unique_preserve_order(rejections)
    return likes, hates


def _normalize_persona_signals(persona: Persona, messages: list[dict[str, str]]) -> Persona:
    negative_material_hits = _extract_cued_keyword_hits(
        messages, _NEGATIVE_CUES, _MATERIAL_KEYWORDS, opposing_cues=_POSITIVE_CUES,
    )
    negative_style_hits = _extract_cued_keyword_hits(
        messages, _NEGATIVE_CUES, _STYLE_KEYWORDS, opposing_cues=_POSITIVE_CUES,
    )

    normalized = persona.model_copy(deep=True)
    normalized.material_preferences = [
        material for material in normalized.material_preferences if material.lower() not in negative_material_hits
    ]
    normalized.style_preferences = [
        style for style in normalized.style_preferences if style.lower() not in negative_style_hits
    ]

    normalized.hates = _unique_preserve_order(
        [
            *normalized.hates,
            *negative_material_hits,
            *negative_style_hits,
        ]
    )

    normalized.likes = [
        like
        for like in _unique_preserve_order(normalized.likes)
        if like.lower() not in negative_material_hits and like.lower() not in negative_style_hits
    ]
    return normalized


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


def _conversation_transcript(messages: list[dict[str, str]]) -> str:
    transcript_lines: list[str] = []
    for message in messages:
        role = message.get("role", "unknown").upper()
        content = message.get("content", "").strip()
        if content:
            transcript_lines.append(f"{role}: {content}")
    return "\n".join(transcript_lines)


def build_anthropic_messages(messages: list[dict[str, str]]) -> list[MessageParam]:
    normalized_messages: list[MessageParam] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "").strip()
        if role not in {"user", "assistant"} or not content:
            continue

        if normalized_messages and normalized_messages[-1]["role"] == role:
            normalized_messages[-1]["content"] = (
                f"{normalized_messages[-1]['content']}\n\n{content}"
            )
            continue

        normalized_messages.append(cast("MessageParam", {"role": role, "content": content}))

    return normalized_messages


def _heuristic_persona(messages: list[dict[str, str]]) -> Persona:
    from app.schemas.persona import Persona

    user_text = " ".join(message.get("content", "") for message in messages if message.get("role") == "user").lower()
    categories = _extract_mapped_keywords(user_text, _CATEGORY_KEYWORDS)
    project_type = _extract_first_mapping(user_text, _PROJECT_KEYWORDS)
    if project_type in _ALLOWED_CATEGORIES and project_type not in categories:
        categories.append(project_type)

    styles = _unique_preserve_order(_extract_keywords(user_text, _STYLE_KEYWORDS))
    materials = _unique_preserve_order(_extract_keywords(user_text, _MATERIAL_KEYWORDS))
    liked_colors = _extract_cued_keyword_hits(
        messages, _POSITIVE_CUES, _COLOR_KEYWORDS,
        opposing_cues=_NEGATIVE_CUES, skip_if_negated=True,
    )
    disliked_colors = _extract_cued_keyword_hits(
        messages, _NEGATIVE_CUES, _COLOR_KEYWORDS, opposing_cues=_POSITIVE_CUES,
    )
    approvals = _extract_cued_phrases(messages, _POSITIVE_CUES, skip_if_negated=True)
    rejections = _extract_cued_phrases(messages, _NEGATIVE_CUES)
    likes, hates = _derive_taste_descriptors(
        categories=categories,
        styles=styles,
        materials=materials,
        approvals=[*approvals, *liked_colors],
        rejections=[*rejections, *disliked_colors],
    )

    persona = Persona(
        project_type=project_type,
        budget_tier=_extract_first_mapping(user_text, _BUDGET_KEYWORDS),
        role=_extract_first_mapping(user_text, _ROLE_KEYWORDS),
        likes=likes,
        hates=hates,
        style_preferences=styles,
        material_preferences=materials,
        categories=categories,
        rejections=rejections,
        approvals=approvals,
    )
    return _normalize_persona_signals(persona, messages)


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
            messages=build_anthropic_messages(messages)
            or [cast("MessageParam", {"role": "user", "content": _conversation_transcript(messages)})],
        )
    except Exception as exc:
        raise ExternalServiceError("claude", "Failed to extract persona") from exc

    raw_text = anthropic_response_text(getattr(response, "content", []))
    payload = extract_json_object(raw_text)
    return _normalize_persona_signals(Persona.model_validate(payload), messages)


def persona_to_text(persona: Persona) -> str:
    """Render persona into a compact embedding prompt."""
    fragments: list[str] = []

    if persona.likes:
        fragments.append(f"Taste likes: {', '.join(persona.likes)}.")
    if persona.hates:
        fragments.append(f"Taste dislikes: {', '.join(persona.hates)}.")
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
    count += len(_unique_preserve_order(persona.likes))
    count += len(_unique_preserve_order(persona.hates))
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

    taste_target = merged.likes if signal == "like" else merged.hates
    taste_target.extend(style_hits)
    taste_target.extend(material_hits)
    taste_target.append(product.name)

    merged.categories = _unique_preserve_order(merged.categories)
    merged.likes = _unique_preserve_order(merged.likes)
    merged.hates = _unique_preserve_order(merged.hates)
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

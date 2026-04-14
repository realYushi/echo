from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.persona import Persona
from app.schemas.product import Product
from app.services import persona as persona_service

if TYPE_CHECKING:
    from pytest import MonkeyPatch


async def test_extract_persona_uses_heuristic_when_client_missing(sample_messages: list[dict[str, str]]) -> None:
    persona = await persona_service.extract_persona(sample_messages, client=None)

    assert persona.project_type == "kitchen"
    assert "modern" in persona.likes
    assert "modern" in persona.style_preferences
    assert "kitchen" in persona.categories


async def test_embed_persona_renders_persona_summary(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    async def fake_get_clip_embedding(text: str) -> list[float]:
        captured["text"] = text
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(persona_service, "get_clip_embedding", fake_get_clip_embedding)
    persona = Persona(
        project_type="kitchen",
        budget_tier="premium",
        likes=["warm minimalism", "oak"],
        hates=["glossy finishes"],
        style_preferences=["modern"],
        material_preferences=["oak"],
        approvals=["warm finishes"],
    )

    embedding = await persona_service.embed_persona(persona)

    assert embedding == [0.1, 0.2, 0.3]
    assert "Taste likes: warm minimalism, oak." in captured["text"]
    assert "Taste dislikes: glossy finishes." in captured["text"]
    assert "Project type: kitchen." in captured["text"]
    assert "Preferred materials: oak." in captured["text"]


def test_apply_feedback_merges_product_tags() -> None:
    persona = Persona(project_type="bathroom")
    product = Product(
        id="lighting-001",
        name="Cascading Crystal Chandelier",
        category="lighting",
        subcategory="chandelier",
        tags=["luxury", "crystal", "lighting"],
        budget_tier="premium",
        image_url="https://example.com/light.png",
        description="A dramatic lighting piece.",
    )

    updated = persona_service.apply_feedback(persona, product, "like")

    assert "lighting" in updated.categories
    assert "luxury" in updated.likes
    assert "luxury" in updated.style_preferences
    assert "Cascading Crystal Chandelier" in updated.approvals


async def test_extract_persona_keeps_negated_materials_out_of_positive_preferences() -> None:
    messages = [
        {"role": "user", "content": "I want bold furniture for my living room."},
        {"role": "assistant", "content": "What should I avoid?"},
        {"role": "user", "content": "I don't like wood or leather."},
    ]

    persona = await persona_service.extract_persona(messages, client=None)

    assert "wood" not in persona.material_preferences
    assert "leather" not in persona.material_preferences
    assert "wood" in persona.hates
    assert "leather" in persona.hates

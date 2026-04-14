from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.persona import Persona
from app.schemas.product import Product
from app.services import persona as persona_service

if TYPE_CHECKING:
    from pytest import MonkeyPatch


async def test_post_process_messages_returns_has_new_signals_true_when_client_missing(
    sample_messages: list[dict[str, str]],
) -> None:
    result = await persona_service.post_process_messages(sample_messages, client=None, model="stub-model")

    assert result["has_new_signals"] is True
    assert result["filtered_signals"] != ""


async def test_build_persona_returns_empty_when_client_missing() -> None:
    persona = await persona_service.build_persona("likes modern, hates glossy", None, client=None, model="stub-model")

    assert persona.likes == []
    assert persona.hates == []
    assert persona.budget_tier is None


async def test_build_persona_returns_current_persona_when_client_missing() -> None:
    current = Persona(likes=["warm minimalism"], budget_tier="premium")

    persona = await persona_service.build_persona("some signals", current, client=None, model="stub-model")

    assert persona.likes == ["warm minimalism"]
    assert persona.budget_tier == "premium"


async def test_embed_persona_renders_persona_summary(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    async def fake_get_clip_embedding(text: str) -> list[float]:
        captured["text"] = text
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(persona_service, "get_clip_embedding", fake_get_clip_embedding)
    persona = Persona(
        budget_tier="premium",
        likes=["warm minimalism", "oak"],
        hates=["glossy finishes"],
        approvals=["warm finishes"],
    )

    embedding = await persona_service.embed_persona(persona)

    assert embedding == [0.1, 0.2, 0.3]
    assert "Taste likes: warm minimalism, oak." in captured["text"]
    assert "Taste dislikes: glossy finishes." in captured["text"]
    assert "Budget tier: premium." in captured["text"]
    assert "Approved products: warm finishes." in captured["text"]


def test_apply_feedback_merges_product_tags() -> None:
    persona = Persona()
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

    assert "luxury" in updated.likes
    assert "crystal" in updated.likes
    assert "Cascading Crystal Chandelier" in updated.approvals
    assert "Cascading Crystal Chandelier" in updated.likes


def test_apply_feedback_dislike_merges_into_hates() -> None:
    persona = Persona()
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

    updated = persona_service.apply_feedback(persona, product, "dislike")

    assert "luxury" in updated.hates
    assert "Cascading Crystal Chandelier" in updated.rejections
    assert "Cascading Crystal Chandelier" in updated.hates


def test_persona_signal_count() -> None:
    persona = Persona(
        budget_tier="premium",
        likes=["modern", "oak"],
        hates=["glossy"],
        approvals=["Product A"],
        rejections=["Product B"],
    )

    assert persona_service.persona_signal_count(persona) == 6


def test_persona_signal_count_empty() -> None:
    persona = Persona()

    assert persona_service.persona_signal_count(persona) == 0

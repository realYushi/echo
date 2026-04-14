from __future__ import annotations

from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient

from app.agent.graph import run_agent_turn
from app.config import Settings
from app.schemas.persona import Persona
from app.schemas.product import Product, Recommendation
from app.services.persona import PostProcessResult

if TYPE_CHECKING:
    from pytest import MonkeyPatch

    from app.agent.state import AgentState


def _fake_query_response() -> object:
    point = type(
        "Point",
        (),
        {
            "payload": Product(
                id="kitchen-001",
                name="Chimney Range Hood",
                category="kitchen",
                subcategory="range-hood",
                tags=["professional", "kitchen", "stainless-steel"],
                budget_tier="premium",
                image_url="https://example.com/range-hood.png",
                description="Ventilation for a premium kitchen.",
            ).model_dump(),
            "score": 0.82,
        },
    )
    return type("Response", (), {"points": [point]})()


async def test_run_agent_turn_generates_persona_and_recommendations(
    monkeypatch: MonkeyPatch,
    sample_messages: list[dict[str, str]],
) -> None:
    from app.agent import nodes

    async def fake_post_process_messages(
        messages: list[dict[str, str]],
        *,
        client: object,
        model: str,
    ) -> PostProcessResult:
        return PostProcessResult(has_new_signals=True, filtered_signals="likes modern, kitchen reno")

    async def fake_build_persona_service(
        filtered_signals: str,
        current_persona: Persona | None,
        *,
        client: object,
        model: str,
    ) -> Persona:
        return Persona(
            likes=["modern", "oak"],
            budget_tier="premium",
        )

    async def fake_embed_persona(persona: Persona) -> list[float]:
        return [0.3, 0.4, 0.5]

    monkeypatch.setattr(nodes, "post_process_messages", fake_post_process_messages)
    monkeypatch.setattr(nodes, "build_persona_service", fake_build_persona_service)
    monkeypatch.setattr(nodes, "embed_persona_service", fake_embed_persona)
    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")

    async def fake_query_points(
        *,
        collection_name: str,
        query: list[float],
        limit: int,
        score_threshold: float,
    ) -> object:
        assert collection_name == "products"
        assert query == [0.3, 0.4, 0.5]
        assert limit == 6
        assert score_threshold == 0.45
        return _fake_query_response()

    monkeypatch.setattr(qdrant_client, "query_points", fake_query_points)

    settings = Settings(
        anthropic_model="stub-model",
        anthropic_post_process_model="stub-haiku",
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
        min_recommendation_signals=2,
    )
    state: AgentState = {"messages": sample_messages, "session_id": "session-1"}

    result = await run_agent_turn(
        state,
        settings=settings,
        qdrant_client=qdrant_client,
        anthropic_client=None,
    )

    assert result["persona"] is not None
    assert "modern" in result["persona"].likes
    assert result["assistant_message"]
    assert result["suggestions"]
    assert result["messages"][-1]["role"] == "assistant"
    assert len(result["recommendations"]) == 1
    assert isinstance(result["recommendations"][0], Recommendation)


async def test_run_agent_turn_applies_feedback_and_refreshes_recommendations(monkeypatch: MonkeyPatch) -> None:
    from app.agent import nodes

    async def fake_embed_persona(persona: Persona) -> list[float]:
        return [0.6, 0.1, 0.2]

    monkeypatch.setattr(nodes, "embed_persona_service", fake_embed_persona)
    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")

    async def fake_query_points(
        *,
        collection_name: str,
        query: list[float],
        limit: int,
        score_threshold: float,
    ) -> object:
        assert collection_name == "products"
        assert query == [0.6, 0.1, 0.2]
        assert limit == 6
        assert score_threshold == 0.45
        return _fake_query_response()

    monkeypatch.setattr(qdrant_client, "query_points", fake_query_points)

    settings = Settings(
        anthropic_model="stub-model",
        anthropic_post_process_model="stub-haiku",
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
        min_recommendation_signals=2,
    )
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "I want dramatic lighting."},
            {"role": "assistant", "content": "Great, what should I avoid?"},
        ],
        "session_id": "session-2",
        "persona": Persona(likes=["warm"]),
        "persona_embedding": [0.2, 0.2, 0.2],
        "pending_feedback": {"product_id": "lighting-001", "signal": "like"},
    }

    result = await run_agent_turn(
        state,
        settings=settings,
        qdrant_client=qdrant_client,
        anthropic_client=None,
    )

    assert result["pending_feedback"] is None
    assert result["persona"] is not None
    assert "Cascading Crystal Chandelier" in result["persona"].approvals
    assert result["suggestions"]
    assert result["recommendations"]


async def test_run_agent_turn_first_substantive_turn_produces_fallback_reply() -> None:
    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")
    settings = Settings(
        anthropic_model="stub-model",
        anthropic_post_process_model="stub-haiku",
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
        min_recommendation_signals=2,
    )
    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "I wanna find something for my kitchen",
            }
        ],
        "session_id": "session-3",
    }

    result = await run_agent_turn(
        state,
        settings=settings,
        qdrant_client=qdrant_client,
        anthropic_client=None,
    )

    assert result["assistant_message"]
    assert result["persona"] is not None


async def test_run_agent_turn_follow_up_turn_produces_reply() -> None:
    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")
    settings = Settings(
        anthropic_model="stub-model",
        anthropic_post_process_model="stub-haiku",
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
        min_recommendation_signals=2,
    )
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "Hi — I can help narrow this down fast."},
            {"role": "user", "content": "i wanna find some thing for my kitchen"},
        ],
        "session_id": "session-4",
    }

    result = await run_agent_turn(
        state,
        settings=settings,
        qdrant_client=qdrant_client,
        anthropic_client=None,
    )

    assert result["assistant_message"]
    assert result["persona"] is not None


async def test_run_agent_turn_handles_small_talk() -> None:
    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")
    settings = Settings(
        anthropic_model="stub-model",
        anthropic_post_process_model="stub-haiku",
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
        min_recommendation_signals=2,
    )
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "Hi — I can help narrow this down fast."},
            {"role": "user", "content": "how are you"},
        ],
        "session_id": "session-5",
    }

    result = await run_agent_turn(
        state,
        settings=settings,
        qdrant_client=qdrant_client,
        anthropic_client=None,
    )

    assert "Doing well" in result["assistant_message"]
    assert "products" in result["assistant_message"].lower()

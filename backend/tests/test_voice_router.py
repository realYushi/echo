from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_anthropic_client, get_qdrant_client, get_settings
from app.main import create_app
from app.schemas.persona import Persona
from app.schemas.product import Product, Recommendation
from app.services.session import get_session, save_session


def _test_settings(**overrides: Any) -> Settings:
    defaults: dict[str, Any] = {
        "qdrant_collection": "products",
        "recommendation_limit": 6,
        "recommendation_score_threshold": 0.45,
        "min_recommendation_signals": 2,
        "gemini_api_key": "test-gemini-key",
        "gemini_live_model": "gemini-3.1-flash-live-preview",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _sample_product() -> Product:
    return Product(
        id="lighting-001",
        name="Cascading Crystal Chandelier",
        category="lighting",
        subcategory="chandelier",
        tags=["luxury", "crystal", "lighting"],
        budget_tier="premium",
        image_url="https://example.com/light.png",
        description="A dramatic lighting piece.",
    )


def _sample_recommendation() -> Recommendation:
    return Recommendation(product=_sample_product(), score=0.88)


# ---------------------------------------------------------------------------
# Token endpoint
# ---------------------------------------------------------------------------


async def test_voice_token_returns_token_and_model() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: _test_settings()

    with patch(
        "app.routers.voice.create_ephemeral_token",
        new_callable=AsyncMock,
        return_value=("auth_tokens/abc123", "gemini-3.1-flash-live-preview"),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/api/voice/token")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "auth_tokens/abc123"
    assert data["model"] == "gemini-3.1-flash-live-preview"


async def test_voice_token_returns_502_when_api_key_missing() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: _test_settings(gemini_api_key="")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/voice/token")

    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "EXTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Transcript endpoint
# ---------------------------------------------------------------------------


class FakeQdrantClient:
    def __init__(self) -> None:
        self.queries: list[list[float]] = []

    async def query_points(
        self,
        *,
        collection_name: str,
        query: list[float],
        limit: int,
        score_threshold: float,
    ) -> object:
        self.queries.append(query)
        point = type(
            "Point",
            (),
            {"payload": _sample_product().model_dump(), "score": 0.88},
        )
        return type("Response", (), {"points": [point]})()


@pytest.fixture
def _pipeline_mocks(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    post_process = AsyncMock(
        return_value={"has_new_signals": True, "filtered_signals": "likes warm minimalism, oak"},
    )
    build = AsyncMock(
        return_value=Persona(
            budget_tier="premium",
            likes=["warm minimalism", "oak"],
            hates=[],
            approvals=[],
            rejections=[],
        ),
    )
    embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

    monkeypatch.setattr("app.routers.voice.post_process_messages", post_process)
    monkeypatch.setattr("app.routers.voice.build_persona", build)
    monkeypatch.setattr("app.routers.voice.embed_persona", embed)

    return {"post_process": post_process, "build": build, "embed": embed}


async def test_voice_transcript_runs_full_pipeline(_pipeline_mocks: dict[str, AsyncMock]) -> None:
    app = create_app()
    fake_qdrant = FakeQdrantClient()
    app.dependency_overrides[get_settings] = lambda: _test_settings()
    app.dependency_overrides[get_qdrant_client] = lambda: fake_qdrant
    app.dependency_overrides[get_anthropic_client] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/voice/transcript",
            json={
                "sessionId": "voice-session-1",
                "messages": [
                    {"role": "user", "content": "I love warm minimalist design"},
                    {"role": "assistant", "content": "Great taste! Tell me more about materials."},
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["sessionId"] == "voice-session-1"
    assert data["persona"]["budgetTier"] == "premium"
    assert data["persona"]["likes"] == ["warm minimalism", "oak"]
    assert len(data["recommendations"]) == 1

    saved = get_session("voice-session-1")
    assert saved is not None
    assert len(saved["messages"]) == 2


async def test_voice_transcript_skips_persona_build_when_no_new_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app()
    fake_qdrant = FakeQdrantClient()
    app.dependency_overrides[get_settings] = lambda: _test_settings()
    app.dependency_overrides[get_qdrant_client] = lambda: fake_qdrant
    app.dependency_overrides[get_anthropic_client] = lambda: None

    post_process = AsyncMock(
        return_value={"has_new_signals": False, "filtered_signals": ""},
    )
    build = AsyncMock()
    embed = AsyncMock(return_value=[])

    monkeypatch.setattr("app.routers.voice.post_process_messages", post_process)
    monkeypatch.setattr("app.routers.voice.build_persona", build)
    monkeypatch.setattr("app.routers.voice.embed_persona", embed)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/voice/transcript",
            json={
                "sessionId": "voice-no-signals",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

    assert response.status_code == 200
    build.assert_not_called()


async def test_voice_transcript_appends_to_existing_session(
    _pipeline_mocks: dict[str, AsyncMock],
) -> None:
    save_session(
        "voice-existing",
        {
            "session_id": "voice-existing",
            "messages": [{"role": "user", "content": "I like oak furniture"}],
            "persona": Persona(likes=["oak"]),
            "persona_embedding": [0.1, 0.2],
            "recommendations": [],
        },
    )

    app = create_app()
    fake_qdrant = FakeQdrantClient()
    app.dependency_overrides[get_settings] = lambda: _test_settings()
    app.dependency_overrides[get_qdrant_client] = lambda: fake_qdrant
    app.dependency_overrides[get_anthropic_client] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/voice/transcript",
            json={
                "sessionId": "voice-existing",
                "messages": [{"role": "user", "content": "And I prefer warm tones"}],
            },
        )

    assert response.status_code == 200

    saved = get_session("voice-existing")
    assert saved is not None
    assert len(saved["messages"]) == 2
    assert saved["messages"][0]["content"] == "I like oak furniture"
    assert saved["messages"][1]["content"] == "And I prefer warm tones"


async def test_voice_transcript_returns_empty_recommendations_when_insufficient_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app()
    fake_qdrant = FakeQdrantClient()
    app.dependency_overrides[get_settings] = lambda: _test_settings()
    app.dependency_overrides[get_qdrant_client] = lambda: fake_qdrant
    app.dependency_overrides[get_anthropic_client] = lambda: None

    post_process = AsyncMock(
        return_value={"has_new_signals": True, "filtered_signals": "oak"},
    )
    build = AsyncMock(
        return_value=Persona(likes=["oak"]),
    )
    embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

    monkeypatch.setattr("app.routers.voice.post_process_messages", post_process)
    monkeypatch.setattr("app.routers.voice.build_persona", build)
    monkeypatch.setattr("app.routers.voice.embed_persona", embed)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/voice/transcript",
            json={
                "sessionId": "voice-low-signals",
                "messages": [{"role": "user", "content": "I like oak"}],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] == []
    assert fake_qdrant.queries == []

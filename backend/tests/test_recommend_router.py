from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_qdrant_client, get_settings
from app.main import create_app
from app.schemas.persona import Persona
from app.schemas.product import Product, Recommendation
from app.services.session import save_session


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
        assert collection_name == "products"
        assert limit == 6
        assert score_threshold == 0.45

        point = type(
            "Point",
            (),
            {
                "payload": Product(
                    id="lighting-001",
                    name="Cascading Crystal Chandelier",
                    category="lighting",
                    subcategory="chandelier",
                    tags=["luxury", "crystal", "lighting"],
                    budget_tier="premium",
                    image_url="https://example.com/light.png",
                    description="A dramatic lighting piece.",
                ).model_dump(),
                "score": 0.88,
            },
        )
        return type("Response", (), {"points": [point]})()


async def test_recommend_uses_session_embedding_when_request_embedding_missing() -> None:
    app = create_app()
    fake_qdrant = FakeQdrantClient()
    app.dependency_overrides[get_settings] = lambda: Settings(
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
    )
    app.dependency_overrides[get_qdrant_client] = lambda: fake_qdrant

    recommendation = Recommendation(
        product=Product(
            id="lighting-001",
            name="Cascading Crystal Chandelier",
            category="lighting",
            subcategory="chandelier",
            tags=["luxury", "crystal", "lighting"],
            budget_tier="premium",
            image_url="https://example.com/light.png",
            description="A dramatic lighting piece.",
        ),
        score=0.88,
    )
    save_session(
        "session-pr5",
        {
            "session_id": "session-pr5",
            "messages": [],
            "persona": Persona(categories=["lighting"], approvals=["Cascading Crystal Chandelier"]),
            "persona_embedding": [0.2, 0.3, 0.4],
            "recommendations": [recommendation],
        },
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/recommend", json={"sessionId": "session-pr5"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "product": {
                "id": "lighting-001",
                "name": "Cascading Crystal Chandelier",
                "category": "lighting",
                "subcategory": "chandelier",
                "tags": ["luxury", "crystal", "lighting"],
                "budgetTier": "premium",
                "imageUrl": "https://example.com/light.png",
                "description": "A dramatic lighting piece.",
            },
            "score": 0.88,
        }
    ]
    assert fake_qdrant.queries == [[0.2, 0.3, 0.4]]


async def test_recommend_returns_empty_list_without_request_or_session_embedding() -> None:
    app = create_app()
    fake_qdrant = FakeQdrantClient()
    app.dependency_overrides[get_settings] = lambda: Settings(
        qdrant_collection="products",
        recommendation_limit=6,
        recommendation_score_threshold=0.45,
    )
    app.dependency_overrides[get_qdrant_client] = lambda: fake_qdrant

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/recommend", json={"sessionId": "missing-session"})

    assert response.status_code == 200
    assert response.json() == []
    assert fake_qdrant.queries == []

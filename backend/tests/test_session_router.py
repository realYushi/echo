from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.schemas.persona import Persona
from app.schemas.product import Product, Recommendation
from app.services.session import save_session


async def test_get_session_snapshot_returns_saved_state() -> None:
    app = create_app()
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
        "session-pr6",
        {
            "session_id": "session-pr6",
            "messages": [
                {"role": "user", "content": "I want sculptural lighting."},
                {"role": "assistant", "content": "What should I avoid?"},
            ],
            "persona": Persona(
                likes=["sculptural"],
                rejections=["glossy finishes"],
            ),
            "persona_embedding": [0.2, 0.3, 0.4],
            "recommendations": [recommendation],
        },
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/sessions/session-pr6")

    assert response.status_code == 200
    assert response.json() == {
        "sessionId": "session-pr6",
        "messages": [
            {"role": "user", "content": "I want sculptural lighting."},
            {"role": "assistant", "content": "What should I avoid?"},
        ],
        "persona": {
            "budgetTier": None,
            "likes": ["sculptural"],
            "hates": [],
            "approvals": [],
            "rejections": ["glossy finishes"],
        },
        "recommendations": [
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
        ],
    }


async def test_get_session_snapshot_returns_empty_state_for_missing_session() -> None:
    app = create_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/sessions/missing-session")

    assert response.status_code == 200
    assert response.json() == {
        "sessionId": "missing-session",
        "messages": [],
        "persona": None,
        "recommendations": [],
    }

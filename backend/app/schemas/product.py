from __future__ import annotations

from typing import Literal

from app.schemas.base import CamelModel


class Product(CamelModel):
    """A product in the catalog."""

    id: str
    name: str
    category: str
    subcategory: str
    tags: list[str]
    budget_tier: str
    image_url: str
    description: str


class Recommendation(CamelModel):
    """A product recommendation with relevance score."""

    product: Product
    score: float


class FeedbackRequest(CamelModel):
    """User feedback on a recommended product."""

    product_id: str
    signal: Literal["like", "dislike"]
    session_id: str


class RecommendRequest(CamelModel):
    """Request body for the recommend endpoint."""

    session_id: str
    persona_embedding: list[float]

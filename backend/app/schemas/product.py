from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Product(BaseModel):
    """A product in the catalog."""

    id: str
    name: str
    category: str
    subcategory: str
    tags: list[str]
    budget_tier: str
    image_url: str
    description: str


class Recommendation(BaseModel):
    """A product recommendation with relevance score."""

    product: Product
    score: float


class FeedbackRequest(BaseModel):
    """User feedback on a recommended product."""

    product_id: str
    signal: Literal["like", "dislike"]

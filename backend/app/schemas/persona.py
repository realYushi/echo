from __future__ import annotations

from app.schemas.base import CamelModel


class Persona(CamelModel):
    """User taste persona extracted from conversation signals."""

    budget_tier: str | None = None
    likes: list[str] = []
    hates: list[str] = []
    approvals: list[str] = []
    rejections: list[str] = []

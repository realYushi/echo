from __future__ import annotations

from app.schemas.base import CamelModel


class Persona(CamelModel):
    """User taste persona extracted from conversation signals."""

    project_type: str | None = None
    budget_tier: str | None = None
    role: str | None = None
    style_preferences: list[str] = []
    material_preferences: list[str] = []
    categories: list[str] = []
    rejections: list[str] = []
    approvals: list[str] = []

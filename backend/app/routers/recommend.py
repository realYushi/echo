from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

if TYPE_CHECKING:
    from app.schemas.persona import Persona

router = APIRouter()


@router.post("/recommend")
async def recommend(persona: Persona) -> dict[str, list[object]]:
    """Return product recommendations based on persona embedding. Stub implementation."""
    return {"recommendations": []}

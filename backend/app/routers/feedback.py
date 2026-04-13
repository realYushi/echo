from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

if TYPE_CHECKING:
    from app.schemas.product import FeedbackRequest

router = APIRouter()


@router.post("/feedback")
async def feedback(request: FeedbackRequest) -> dict[str, str]:
    """Record user feedback on a product recommendation. Stub implementation."""
    return {"status": "ok", "message": "Feedback endpoint stub -- not yet implemented"}

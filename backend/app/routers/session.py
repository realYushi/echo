from __future__ import annotations

from fastapi import APIRouter

from app.schemas.session import SessionSnapshot  # noqa: TC001 - FastAPI resolves annotations at runtime
from app.services.session import get_session_snapshot

router = APIRouter()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> SessionSnapshot:
    """Return the stored discovery state for a session."""
    return get_session_snapshot(session_id)

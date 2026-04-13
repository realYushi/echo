from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.state import AgentState


_sessions: dict[str, AgentState] = {}


def get_session(session_id: str) -> AgentState | None:
    """Return the stored agent state for a session, or None if not found."""
    return _sessions.get(session_id)


def save_session(session_id: str, state: AgentState) -> None:
    """Store the agent state after a completed turn."""
    _sessions[session_id] = state

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from app.schemas.session import SessionMessage, SessionMessageRole, SessionSnapshot

if TYPE_CHECKING:
    from app.agent.state import AgentState


_sessions: dict[str, AgentState] = {}


def get_session(session_id: str) -> AgentState | None:
    """Return the stored agent state for a session, or None if not found."""
    return _sessions.get(session_id)


def save_session(session_id: str, state: AgentState) -> None:
    """Store the agent state after a completed turn."""
    _sessions[session_id] = state


def clear_sessions() -> None:
    """Clear all stored sessions. Intended for test isolation."""
    _sessions.clear()


def get_session_snapshot(session_id: str) -> SessionSnapshot:
    """Build a frontend-facing snapshot for the requested session."""
    state = get_session(session_id)
    if state is None:
        return SessionSnapshot(
            session_id=session_id,
            messages=[],
            persona=None,
            recommendations=[],
        )

    messages: list[SessionMessage] = []
    for message in state.get("messages", []):
        role = message.get("role")
        content = message.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        messages.append(
            SessionMessage(role=cast("SessionMessageRole", role), content=content),
        )

    return SessionSnapshot(
        session_id=session_id,
        messages=messages,
        persona=state.get("persona"),
        recommendations=state.get("recommendations", []),
    )

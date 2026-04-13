from __future__ import annotations

from pydantic import BaseModel


class Message(BaseModel):
    """A single chat message."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    messages: list[Message]
    session_id: str

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.state import AgentState


async def greet(state: AgentState) -> AgentState:
    """Generate greeting and initial discovery questions."""
    raise NotImplementedError


async def discover(state: AgentState) -> AgentState:
    """Process user message in discovery conversation."""
    raise NotImplementedError


async def extract_persona(state: AgentState) -> AgentState:
    """Extract persona JSON from conversation."""
    raise NotImplementedError


async def embed_persona(state: AgentState) -> AgentState:
    """Convert persona to embedding vector."""
    raise NotImplementedError


async def recommend(state: AgentState) -> AgentState:
    """Retrieve recommendations based on persona embedding."""
    raise NotImplementedError


async def feedback(state: AgentState) -> AgentState:
    """Process user feedback on recommendations."""
    raise NotImplementedError

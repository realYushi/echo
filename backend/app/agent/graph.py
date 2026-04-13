from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.graph import StateGraph


def build_graph() -> StateGraph:
    """Build the 6-node LangGraph agent graph.

    Nodes: greet -> discover -> extract_persona -> embed_persona -> recommend -> feedback
    """
    raise NotImplementedError

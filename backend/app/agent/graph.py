from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Protocol, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import build_persona, discover, embed_persona, feedback, greet, post_process, recommend
from app.agent.state import AgentState

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from qdrant_client import AsyncQdrantClient

    from app.config import Settings


class CompiledAgentGraph(Protocol):
    """Compiled graph interface used by the API layer."""

    async def ainvoke(
        self,
        state_input: AgentState | None,
        config: object | None = None,
        **kwargs: object,
    ) -> AgentState: ...


_CHECKPOINTER: InMemorySaver | None = None


def _get_checkpointer() -> InMemorySaver:
    global _CHECKPOINTER  # noqa: PLW0603
    if _CHECKPOINTER is None:
        _CHECKPOINTER = InMemorySaver()
    return _CHECKPOINTER


def build_graph(
    *,
    settings: Settings,
    qdrant_client: AsyncQdrantClient,
    anthropic_client: AsyncAnthropic | None,
) -> object:
    """Build the LangGraph agent graph.

    Nodes: greet -> discover -> post_process -> [build_persona] -> embed_persona -> recommend -> feedback
    """
    builder = StateGraph(AgentState)
    builder.add_node("greet", partial(greet, anthropic_client=anthropic_client, settings=settings))
    builder.add_node("discover", partial(discover, anthropic_client=anthropic_client, settings=settings))
    builder.add_node("post_process", partial(post_process, anthropic_client=anthropic_client, settings=settings))
    builder.add_node("build_persona", partial(build_persona, anthropic_client=anthropic_client, settings=settings))
    builder.add_node("embed_persona", embed_persona)
    builder.add_node("recommend", partial(recommend, qdrant_client=qdrant_client, settings=settings))
    builder.add_node("feedback", partial(feedback, qdrant_client=qdrant_client, settings=settings))

    builder.add_edge(START, "greet")
    builder.add_edge("greet", "discover")
    builder.add_edge("discover", "post_process")
    builder.add_conditional_edges(
        "post_process",
        lambda state: "build_persona" if state.get("has_new_signals", True) else "embed_persona",
    )
    builder.add_edge("build_persona", "embed_persona")
    builder.add_edge("embed_persona", "recommend")
    builder.add_edge("recommend", "feedback")
    builder.add_edge("feedback", END)

    return builder.compile(checkpointer=_get_checkpointer())


async def run_agent_turn(
    state: AgentState,
    *,
    settings: Settings,
    qdrant_client: AsyncQdrantClient,
    anthropic_client: AsyncAnthropic | None,
) -> AgentState:
    """Run one graph turn using the session ID as the LangGraph thread ID."""
    normalized_state: AgentState = {
        **state,
        "assistant_message": "",
        "suggestions": [],
    }
    graph = cast(
        "CompiledAgentGraph",
        build_graph(
            settings=settings,
            qdrant_client=qdrant_client,
            anthropic_client=anthropic_client,
        ),
    )
    return await graph.ainvoke(
        normalized_state,
        config={"configurable": {"thread_id": state["session_id"]}},
    )

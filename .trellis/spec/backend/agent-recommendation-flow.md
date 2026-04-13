# Agent Recommendation Flow

> Executable backend contracts for the PR3 LangGraph persona and recommendation flow.

---

## Scenario: LangGraph Persona And Recommendation Flow

### 1. Scope / Trigger

- Trigger: Any change to `app/agent/*`, `app/services/persona.py`, `app/services/recommendation.py`, `app/services/catalog.py`, or router/dependency code that calls the recommendation loop.
- Trigger: Any change to Anthropic model selection, recommendation thresholds, or state fields passed across the chat, recommend, and feedback boundaries.
- Why this needs code-spec depth: this flow crosses agent state, Claude fallback behavior, embedding generation, Qdrant retrieval, and feedback mutation. Drift at any boundary silently changes recommendation behavior.

### 2. Signatures

#### Agent State

```python
class PendingFeedback(TypedDict):
    product_id: str
    signal: Literal["like", "dislike"]


class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    persona: Persona | None
    persona_embedding: list[float]
    recommendations: list[Recommendation]
    session_id: str
    assistant_message: str
    pending_feedback: PendingFeedback | None
```

#### Graph Entry Points

```python
def build_graph(
    *,
    settings: Settings,
    qdrant_client: AsyncQdrantClient,
    anthropic_client: AsyncAnthropic | None,
) -> object


async def run_agent_turn(
    state: AgentState,
    *,
    settings: Settings,
    qdrant_client: AsyncQdrantClient,
    anthropic_client: AsyncAnthropic | None,
) -> AgentState
```

#### Persona Services

```python
async def extract_persona(
    messages: list[dict[str, str]],
    client: AsyncAnthropic | None,
    model: str | None = None,
) -> Persona


async def embed_persona(persona: Persona) -> list[float]


def persona_signal_count(persona: Persona) -> int


def apply_feedback(persona: Persona, product: Product, signal: str) -> Persona
```

#### Dependency And Settings Contracts

```python
def get_anthropic_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncAnthropic | None
```

```python
class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"
    recommendation_limit: int = 6
    recommendation_score_threshold: float = 0.45
    min_recommendation_signals: int = 2
```

### 3. Contracts

#### Graph Topology

- The graph order is fixed: `greet -> discover -> extract_persona -> embed_persona -> recommend -> feedback`.
- `run_agent_turn()` must call the compiled graph with `config={"configurable": {"thread_id": state["session_id"]}}`.
- `run_agent_turn()` resets `assistant_message` to `""` before invocation so each turn can decide whether a new assistant reply should be generated.

#### Checkpointing Contract

- The current checkpointer is `InMemorySaver`.
- Persistence is keyed by `session_id` via LangGraph `thread_id`.
- This is process-local memory only. It supports same-process thread continuity, not durable restart-safe session recovery.
- Do not write specs or code that assume PostgreSQL-backed checkpoint durability until that storage layer is actually implemented.

#### Agent Node Behavior

- `greet()` only appends an assistant message when the existing message history contains no assistant message.
- `discover()` is a no-op when `assistant_message` is already populated in the current turn.
- `extract_persona()` always writes `state["persona"]`.
- `embed_persona()` returns `persona_embedding=[]` when there is no persona or `persona_signal_count(persona) == 0`.
- `recommend()` returns `recommendations=[]` when either of these is true:
  - `persona_signal_count(persona) < settings.min_recommendation_signals`
  - `persona_embedding` is empty
- `feedback()` is a no-op when `pending_feedback is None`.
- `feedback()` must clear `pending_feedback` after processing, including the missing-product path.

#### Persona Extraction Contract

- `extract_persona()` must never fail closed for normal chat flow.
- If `messages` is empty, return an empty `Persona()`.
- If `client is None` or `model` is empty, log an info fallback event and return the heuristic persona.
- If Claude fails or returns invalid output, log a warning fallback event and return the heuristic persona.
- The Claude extraction prompt expects JSON with these snake_case keys only:
  - `project_type`
  - `budget_tier`
  - `role`
  - `style_preferences`
  - `material_preferences`
  - `categories`
  - `rejections`
  - `approvals`

#### Persona Embedding Contract

- `persona_to_text()` is the only supported transformation from structured persona to embedding input text.
- `embed_persona()` uses CLIP text embeddings on the rendered persona summary, not raw JSON.
- Empty or early-stage personas must still render to a stable fallback sentence instead of an empty string.

#### Feedback Contract

- `pending_feedback.signal` is constrained to `"like"` or `"dislike"`.
- `apply_feedback()` mutates a copied persona, never the input model in place.
- Feedback always adds `product.category` into `persona.categories` if missing.
- Style and material enrichment comes from `product.tags` intersected with the known keyword sets.
- Positive feedback appends `product.name` to `approvals`; negative feedback appends it to `rejections`.
- Deduplication must preserve order across categories, style preferences, material preferences, approvals, and rejections.

#### Runtime Annotation Contract

- `AgentState` must import schema modules at runtime, not behind `TYPE_CHECKING`, because LangGraph resolves `TypedDict` annotations at runtime.
- This is one of the rare approved cases where runtime-only schema imports are preferable to `TYPE_CHECKING` guards.

#### Environment Contract

| Setting | Purpose | Default | Behavior |
|---------|---------|---------|----------|
| `ANTHROPIC_API_KEY` | Enables Claude-backed discovery and persona extraction | `""` | Empty string disables Anthropic and activates heuristic fallback |
| `ANTHROPIC_MODEL` | Claude model name passed to `messages.create()` | `claude-3-5-sonnet-latest` | Used by both discovery reply generation and persona extraction |
| `RECOMMENDATION_LIMIT` | Max number of returned recommendations | `6` | Passed directly to Qdrant query |
| `RECOMMENDATION_SCORE_THRESHOLD` | Minimum Qdrant similarity score | `0.45` | Filters low-similarity products |
| `MIN_RECOMMENDATION_SIGNALS` | Minimum persona signal count before recommendation retrieval | `2` | Prevents low-signal recommendation churn |

### 4. Validation & Error Matrix

| Condition | Expected Behavior | Boundary |
|-----------|-------------------|----------|
| Empty `messages` passed to persona extraction | Return `Persona()` | Service |
| `ANTHROPIC_API_KEY` not configured | `get_anthropic_client()` returns `None`; discovery/persona flow uses fallback paths | Dependency -> Agent |
| Claude request fails | Log warning/info fallback and continue with heuristic persona or canned discovery question | Service / Agent |
| Claude returns non-JSON or wrong JSON shape | Treat as fallback, do not break chat flow | Service |
| Persona has zero signals | `persona_embedding=[]` | Agent |
| Persona signals below threshold | `recommendations=[]` and `recommendations_skipped` log | Agent -> Recommendation |
| `pending_feedback` absent | `feedback()` returns state unchanged | Agent |
| Feedback `product_id` missing from seeded catalog | Log warning, clear `pending_feedback`, leave persona/recommendations otherwise unchanged | Agent -> Catalog |
| Qdrant query fails during recommendation retrieval | Raise `ExternalServiceError("qdrant", ...)` from recommendation service | Service |

### 5. Good / Base / Bad Cases

#### Good

- User gives project type, style, and material signals.
- Persona extraction returns populated fields.
- `persona_signal_count(persona) >= 2`.
- Embedding is generated and Qdrant recommendations are returned.

#### Base

- User gives one weak signal and no Anthropic key is configured.
- Heuristic extraction returns a partial persona.
- Embedding may still be empty or recommendations remain empty because the signal threshold is not met.
- Chat flow continues with a fallback discovery question.

#### Bad

- Claude returns malformed output or Qdrant is unavailable.
- Persona extraction must fall back without breaking the turn.
- Recommendation retrieval may raise a typed external error at the service boundary, but the API layer must convert that into graceful behavior appropriate for the endpoint.

### 6. Tests Required

- `tests/test_persona.py`
  - Assert heuristic extraction populates project and category signals when Anthropic is missing.
  - Assert `embed_persona()` renders the textual summary before CLIP embedding.
  - Assert `apply_feedback()` merges category/tag/product-name signals.
- `tests/test_agent_graph.py`
  - Assert `run_agent_turn()` produces a persona, appends one assistant message, and returns recommendations for a valid high-signal turn.
  - Assert feedback updates persona approvals, clears `pending_feedback`, and refreshes recommendations.
- When adding new state fields:
  - Add at least one graph test proving the field survives a full `run_agent_turn()` invocation.
- When changing thresholds or fallback behavior:
  - Add one positive and one negative-path assertion covering recommendation gating.

### 7. Wrong vs Correct

#### Wrong

```python
if TYPE_CHECKING:
    from app.schemas.persona import Persona


class AgentState(TypedDict, total=False):
    persona: Persona | None
```

- Why wrong: LangGraph resolves the `TypedDict` annotations at runtime. Hiding schema imports behind `TYPE_CHECKING` causes runtime resolution problems.

#### Correct

```python
from app.schemas import persona as persona_schema


class AgentState(TypedDict, total=False):
    persona: persona_schema.Persona | None
```

#### Wrong

```python
async def extract_persona(messages: list[dict[str, str]], client: AsyncAnthropic) -> Persona:
    response = await client.messages.create(...)
    return Persona.model_validate(json.loads(response_text))
```

- Why wrong: this makes the whole chat path dependent on Claude success.

#### Correct

```python
async def extract_persona(
    messages: list[dict[str, str]],
    client: AsyncAnthropic | None,
    model: str | None = None,
) -> Persona:
    heuristic = _heuristic_persona(messages)
    if client is None or not model:
        return heuristic
    try:
        return await _extract_persona_with_claude(messages, client, model)
    except Exception:
        return heuristic
```

---

## Design Decision: Heuristic Fallback Before Full API Wiring

**Context**: The MVP needs a usable discovery loop even when Anthropic is unavailable during local development or partial rollout.

**Decision**: Persona extraction and discovery-question generation both degrade to deterministic local logic when Anthropic is unavailable or fails.

**Why**:
- Keeps the recommendation loop testable without external API access.
- Allows PR3 to establish stable service and graph contracts before SSE/API work lands in PR4.
- Makes failure behavior explicit and testable.

**Consequence**: Recommendation quality may be lower without Anthropic, but the user flow should remain operable.

---

## Scenario: API Layer SSE And Endpoint Contracts

### 1. Scope / Trigger

- Trigger: Any change to `app/routers/*`, `app/schemas/*`, `app/services/session.py`, or SSE event format.
- Trigger: Any change to the frontend `ChatEvent`, `ChatRequest`, `Persona`, `Product`, or `Recommendation` types.
- Why this needs code-spec depth: the API layer is the cross-layer boundary between frontend (camelCase) and backend (snake_case). Drift in serialization, event format, or request shape silently breaks the discovery loop.

### 2. Signatures

#### Chat Endpoint

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
    anthropic_client: Annotated[AsyncAnthropic | None, Depends(get_anthropic_client)],
) -> StreamingResponse
```

#### Recommend Endpoint

```python
@router.post("/recommend")
async def recommend(
    request: RecommendRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> list[dict[str, object]]
```

#### Feedback Endpoint

```python
@router.post("/feedback")
async def feedback(
    request: FeedbackRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> dict[str, object]
```

#### Session Store

```python
def get_session(session_id: str) -> AgentState | None
def save_session(session_id: str, state: AgentState) -> None
```

### 3. Contracts

#### CamelCase Serialization

All API-facing schemas inherit from `CamelModel` (`app/schemas/base.py`) which uses `alias_generator=to_camel` and `populate_by_name=True`. This means:
- Incoming JSON uses camelCase keys (`sessionId`, `personaEmbedding`, `productId`)
- `POST /api/recommend` accepts either an explicit `personaEmbedding` or a bare `sessionId` that resolves the embedding from the server session store
- Outgoing JSON must use camelCase (`projectType`, `budgetTier`, `imageUrl`)
- When serializing manually (SSE events, dict returns), use `model_dump(by_alias=True)`

#### SSE Event Format

The chat endpoint streams `text/event-stream` with this exact format:

```
data: {"type": "token", "content": "<assistant message text>"}\n\n
data: {"type": "persona_update", "persona": {<camelCase Persona>}}\n\n
data: {"type": "done"}\n\n
```

On error:

```
data: {"type": "error", "message": "<user-facing message>"}\n\n
data: {"type": "done"}\n\n
```

Frontend expects these types (from `frontend/src/types/chat.ts`):

```typescript
export type ChatEvent =
  | { type: "token"; content: string }
  | { type: "persona_update"; persona: Persona }
  | { type: "done" }
  | { type: "error"; message: string };
```

#### Request Schemas

| Endpoint | Schema | Fields |
|----------|--------|--------|
| `POST /api/chat` | `ChatRequest` | `sessionId: str`, `message: str`, `persona: Persona \| None` |
| `POST /api/recommend` | `RecommendRequest` | `sessionId: str`, `personaEmbedding: list[float] \| None = None` |
| `POST /api/feedback` | `FeedbackRequest` | `productId: str`, `signal: "like" \| "dislike"`, `sessionId: str` |

#### Response Contracts

| Endpoint | Response |
|----------|----------|
| Chat | SSE stream (see above) |
| Recommend | `Recommendation[]` with camelCase keys. Router uses `request.personaEmbedding` first, then falls back to session-backed `persona_embedding`, and returns `[]` if neither exists |
| Feedback | `{"persona": <camelCase Persona>}` |

#### Session Persistence

- In-memory dict keyed by `session_id` (`app/services/session.py`)
- Chat endpoint loads previous state, appends user message, runs agent turn, saves result
- Feedback endpoint loads session, updates persona + embedding, saves back
- Process-local only -- does not survive restarts (same limitation as `InMemorySaver` checkpointer)

### 4. Validation & Error Matrix

| Condition | Expected Behavior | Boundary |
|-----------|-------------------|----------|
| Agent turn raises any exception | SSE emits `error` event + `done`, does not drop connection | Router (chat) |
| Empty `personaEmbedding` in recommend request and no session-backed embedding | Return `[]` (200) | Router (recommend) |
| Empty `personaEmbedding` in recommend request but session has embedding | Reuse session-backed embedding and return recommendations | Router (recommend) |
| `productId` not found in seed catalog | 404 `NotFoundError` via global handler | Router (feedback) |
| No existing session for `sessionId` in chat | Start fresh (empty messages, null persona) | Router (chat) |
| No existing session for `sessionId` in feedback | Use empty `Persona()`, skip session save | Router (feedback) |

### 5. Good / Base / Bad Cases

#### Good

- User sends 2+ messages, persona accumulates signals, recommend returns 6 products, feedback updates persona and persists to session.

#### Base

- First message in a new session: agent greets, persona is mostly empty, recommendations return empty (insufficient signals).

#### Bad

- Claude API is down: chat falls back to heuristic discovery reply + heuristic persona, SSE stream still completes with `token` + `persona_update` + `done`.
- Qdrant is down: recommend raises `ExternalServiceError`, chat catches it in SSE stream and emits `error` event.

### 6. Tests Required

- `tests/test_chat_router.py`
  - Assert SSE stream contains `token`, `persona_update`, and `done` events for a valid message.
  - Assert error event is emitted when agent turn fails.
  - Assert session state persists across two sequential chat requests.
- `tests/test_recommend_router.py`
  - Assert empty embedding returns `[]`.
  - Assert valid embedding returns camelCase recommendation objects.
  - Assert request body with only `sessionId` reuses the stored session embedding.
- `tests/test_feedback_router.py`
  - Assert 404 for unknown product ID.
  - Assert returned persona contains product name in approvals/rejections.

### 7. Wrong vs Correct

#### Wrong

```python
if TYPE_CHECKING:
    from app.schemas.chat import ChatRequest

@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    ...
```

- Why wrong: `from __future__ import annotations` defers evaluation. FastAPI + Pydantic resolve endpoint annotations at runtime for schema generation. Forward ref `ChatRequest` is not available, causing `PydanticUserError: not fully defined`.

#### Correct

```python
from app.schemas.chat import ChatRequest  # noqa: TC001 - FastAPI resolves at runtime

@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    ...
```

#### Wrong

```python
yield _sse_event({"type": "persona_update", "persona": persona.model_dump()})
```

- Why wrong: `model_dump()` without `by_alias=True` emits snake_case keys (`project_type`), but the frontend expects camelCase (`projectType`).

#### Correct

```python
yield _sse_event({"type": "persona_update", "persona": persona.model_dump(by_alias=True)})

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
    suggestions: list[str]
    pending_feedback: PendingFeedback | None
    has_new_signals: bool
    filtered_signals: str
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
class PostProcessResult(TypedDict):
    has_new_signals: bool
    filtered_signals: str


async def post_process_messages(
    messages: list[dict[str, str]],
    *,
    client: AsyncAnthropic | None,
    model: str,
) -> PostProcessResult


async def build_persona(
    filtered_signals: str,
    current_persona: Persona | None,
    *,
    client: AsyncAnthropic | None,
    model: str,
) -> Persona


async def embed_persona(persona: Persona) -> list[float]


def persona_signal_count(persona: Persona) -> int


def apply_feedback(persona: Persona, product: Product, signal: str) -> Persona


def build_anthropic_messages(messages: list[dict[str, str]]) -> list[MessageParam]


def extract_json_object(raw_text: str) -> dict[str, object]


def anthropic_response_text(content_blocks: object) -> str
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
    anthropic_post_process_model: str = "claude-haiku-4-20250414"
    recommendation_limit: int = 6
    recommendation_score_threshold: float = 0.45
    min_recommendation_signals: int = 2
```

### 3. Contracts

#### Graph Topology

- The graph order is: `greet -> discover -> post_process -> [build_persona] -> embed_persona -> recommend -> feedback`.
- `post_process` has a conditional edge: routes to `build_persona` when `has_new_signals` is true (default), skips to `embed_persona` when false.
- `run_agent_turn()` must call the compiled graph with `config={"configurable": {"thread_id": state["session_id"]}}`.
- `run_agent_turn()` resets `assistant_message` to `""` and `suggestions` to `[]` before invocation so each turn starts clean.

#### Checkpointing Contract

- The current checkpointer is `InMemorySaver`.
- Persistence is keyed by `session_id` via LangGraph `thread_id`.
- This is process-local memory only. It supports same-process thread continuity, not durable restart-safe session recovery.
- Do not write specs or code that assume PostgreSQL-backed checkpoint durability until that storage layer is actually implemented.

#### Agent Node Behavior

- `greet()` only appends an assistant message when the existing message history contains no assistant message. Returns via `_append_assistant_message()`.
- `discover()` is a no-op when `assistant_message` is already populated in the current turn. Returns via `_append_assistant_message()`.
- Both `greet()` and `discover()` use `state.get("persona")` directly as context for Claude replies (no inline persona extraction).
- Discovery replies use Claude's multi-turn message format via `build_anthropic_messages()` and return structured JSON `{"reply": string, "suggestions": string[]}`.
- When Claude is unavailable or fails, `_fallback_discovery_reply()` returns deterministic replies and `_fallback_suggestions()` based on persona completeness stage (likes → budget_tier → hates/rejections).
- `post_process()` writes `has_new_signals` and `filtered_signals` to state.
- `build_persona()` writes `state["persona"]`. Only runs when `has_new_signals` is true.
- `embed_persona()` returns `persona_embedding=[]` when there is no persona or `persona_signal_count(persona) == 0`.
- `recommend()` returns `recommendations=[]` when either of these is true:
  - `persona_signal_count(persona) < settings.min_recommendation_signals`
  - `persona_embedding` is empty
- `feedback()` is a no-op when `pending_feedback is None`.
- `feedback()` must clear `pending_feedback` after processing, including the missing-product path.

#### Post-Processing Contract (Three-Stage Pipeline: Stage 1)

- `post_process_messages()` detects whether the conversation contains new aesthetic taste signals.
- Uses a lightweight model (`anthropic_post_process_model`, default Haiku) for cost efficiency.
- Returns `PostProcessResult(has_new_signals=bool, filtered_signals=str)`.
- Taste signals include: styles, materials, colors, textures, finishes, budget hints, product approvals/rejections by name.
- NOT taste signals (must be filtered out): functional requirements (size, dimensions, capacity, shape, quantity), room context, personal details.
- Must never fail closed: if `client is None`, returns fallback with `has_new_signals=True` and raw conversation transcript.
- If Claude fails or returns unparseable output, logs warning and returns the same fallback.

#### Persona Building Contract (Three-Stage Pipeline: Stage 2)

- `build_persona()` merges filtered signals into the existing persona via Claude.
- Uses the primary model (`anthropic_model`, default Sonnet) for quality.
- Receives `filtered_signals` (text) and `current_persona` (structured), returns a new `Persona`.
- The prompt constrains `budget_tier` to exactly `"budget"`, `"mid"`, `"premium"`, or `null`.
- `likes` and `hates` must contain only portable aesthetic taste descriptors (not functional requirements).
- Must merge new signals into existing persona without losing prior entries.
- Must never fail closed: if `client is None`, returns `current_persona` (or empty `Persona()` if null).
- If Claude fails or returns unparseable output, logs warning and returns the same fallback.

#### Persona Embedding Contract

- `persona_to_text()` is the only supported transformation from structured persona to embedding input text.
- `persona_to_text()` renders likes, hates, budget_tier, approvals, and rejections. Taste descriptors (likes/hates) are the primary embedding signal.
- `embed_persona()` uses CLIP text embeddings on the rendered persona summary, not raw JSON.
- Empty or early-stage personas must still render to a stable fallback sentence instead of an empty string.

#### Utility Function Contracts

- `build_anthropic_messages()` normalizes message dicts into Claude `MessageParam` format: filters to `user`/`assistant` roles only, strips empty content, and merges consecutive same-role messages with `\n\n` separator.
- `extract_json_object()` extracts the first JSON object (`{...}`) from Claude's raw text response via regex, raises `ValueError` if absent or not a dict.
- `anthropic_response_text()` extracts text from Claude `ContentBlock` lists by concatenating blocks where `type == "text"`.

#### Feedback Contract

- `pending_feedback.signal` is constrained to `"like"` or `"dislike"`.
- `apply_feedback()` mutates a copied persona, never the input model in place.
- Positive feedback appends `product.name` to `approvals` and product tags/name to `likes`; negative feedback appends `product.name` to `rejections` and product tags/name to `hates`.
- Deduplication must preserve order across approvals, rejections, likes, and hates.

#### Runtime Annotation Contract

- `AgentState` must import schema modules at runtime, not behind `TYPE_CHECKING`, because LangGraph resolves `TypedDict` annotations at runtime.
- This is one of the rare approved cases where runtime-only schema imports are preferable to `TYPE_CHECKING` guards.

#### Environment Contract

| Setting | Purpose | Default | Behavior |
|---------|---------|---------|----------|
| `ANTHROPIC_API_KEY` | Enables Claude-backed discovery and persona pipeline | `""` | Empty string disables Anthropic and activates fallback paths |
| `ANTHROPIC_MODEL` | Primary Claude model for discovery replies and persona building | `claude-3-5-sonnet-latest` | Used by `discover()` and `build_persona()` |
| `ANTHROPIC_POST_PROCESS_MODEL` | Lightweight model for taste signal detection | `claude-haiku-4-20250414` | Used by `post_process()` only |
| `RECOMMENDATION_LIMIT` | Max number of returned recommendations | `6` | Passed directly to Qdrant query |
| `RECOMMENDATION_SCORE_THRESHOLD` | Minimum Qdrant similarity score | `0.45` | Filters low-similarity products |
| `MIN_RECOMMENDATION_SIGNALS` | Minimum persona signal count before recommendation retrieval | `2` | Prevents low-signal recommendation churn |

### 4. Validation & Error Matrix

| Condition | Expected Behavior | Boundary |
|-----------|-------------------|----------|
| `ANTHROPIC_API_KEY` not configured | `get_anthropic_client()` returns `None`; discovery/persona pipeline uses fallback paths | Dependency -> Agent |
| Post-process Claude request fails | Log warning, return fallback `PostProcessResult(has_new_signals=True, filtered_signals=<transcript>)` | Service |
| Post-process Claude returns non-JSON | Log warning, return same fallback | Service |
| Build-persona Claude request fails | Log warning, return `current_persona` (or empty `Persona()`) | Service |
| Build-persona Claude returns non-JSON or invalid schema | Log warning, return same fallback | Service |
| Discovery Claude request fails | Log warning, use `_fallback_discovery_reply()` | Agent |
| Persona has zero signals | `persona_embedding=[]` | Agent |
| Persona signals below threshold | `recommendations=[]` and `recommendations_skipped` log | Agent -> Recommendation |
| `pending_feedback` absent | `feedback()` returns state unchanged | Agent |
| Feedback `product_id` missing from seeded catalog | Log warning, clear `pending_feedback`, leave persona/recommendations otherwise unchanged | Agent -> Catalog |
| Qdrant query fails during recommendation retrieval | Raise `ExternalServiceError("qdrant", ...)` from recommendation service | Service |

### 5. Good / Base / Bad Cases

#### Good

- User gives taste signals (style, material, budget hints).
- Post-process detects new signals, build-persona populates fields.
- `persona_signal_count(persona) >= 2`.
- Embedding is generated and Qdrant recommendations are returned.

#### Base

- User gives one weak signal and no Anthropic key is configured.
- Post-process fallback returns raw transcript with `has_new_signals=True`.
- Build-persona fallback returns empty `Persona()`.
- Embedding may still be empty or recommendations remain empty because the signal threshold is not met.
- Chat flow continues with a fallback discovery question.

#### Bad

- Claude returns malformed output or Qdrant is unavailable.
- Post-process and build-persona must fall back without breaking the turn.
- Recommendation retrieval may raise a typed external error at the service boundary, but the API layer must convert that into graceful behavior appropriate for the endpoint.

### 6. Tests Required

- `tests/test_persona.py`
  - Assert `post_process_messages()` returns `has_new_signals=True` with transcript when client is None.
  - Assert `build_persona()` returns empty `Persona()` when client is None and no current persona.
  - Assert `build_persona()` returns current persona when client is None and current persona exists.
  - Assert `embed_persona()` renders likes, hates, budget, approvals in the textual summary.
  - Assert `apply_feedback()` merges product tags/name into likes/hates and product name into approvals/rejections.
  - Assert `persona_signal_count()` correctly counts all five fields.
- `tests/test_agent_graph.py`
  - Assert `run_agent_turn()` produces a persona, appends one assistant message, returns suggestions, and returns recommendations for a valid high-signal turn.
  - Assert feedback updates persona approvals, clears `pending_feedback`, and refreshes recommendations.
  - Assert fallback discovery replies produce both content and suggestions for first substantive turn and follow-up turns.
  - Assert small talk produces a redirect reply.
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
async def post_process_messages(messages, *, client, model) -> PostProcessResult:
    response = await client.messages.create(...)
    payload = extract_json_object(anthropic_response_text(response.content))
    return PostProcessResult(has_new_signals=payload["has_new_signals"], ...)
```

- Why wrong: if `client` is None or Claude fails, the entire chat turn crashes. Persona pipeline must never fail closed.

#### Correct

```python
async def post_process_messages(messages, *, client, model) -> PostProcessResult:
    fallback = PostProcessResult(has_new_signals=True, filtered_signals=_conversation_transcript(messages))
    if client is None:
        return fallback
    try:
        response = await client.messages.create(...)
    except Exception as exc:
        await logger.awarn("post_process_claude_failed", error=str(exc))
        return fallback
    # ... parse with fallback on ValueError too
```

#### Wrong

```python
_PERSONA_BUILDER_SYSTEM_PROMPT = """
Return JSON with: budget_tier, likes, hates, approvals, rejections.
likes and hates should include all user preferences.
"""
```

- Why wrong: without explicit constraints, `budget_tier` gets raw values like "no limit" instead of enum values, and `likes`/`hates` get polluted with functional requirements ("seats 4-6 people") that corrupt the portable taste profile.

#### Correct

```python
_PERSONA_BUILDER_SYSTEM_PROMPT = (
    '- budget_tier must be exactly "budget", "mid", "premium", or null.\n'
    '  Map: "no limit"/"luxury" -> "premium"; "affordable" -> "budget".\n'
    "- likes and hates are portable aesthetic taste descriptors: "
    "styles, materials, colors, textures, finishes.\n"
    "  NOT functional requirements (size, shape, capacity, room type).\n"
)
```

---

## Design Decision: Three-Stage Persona Pipeline

**Context**: The original single-step `extract_persona()` used heuristic keyword dictionaries that were brittle and produced low-quality signals. The persona needed to be rebuilt every turn regardless of whether new taste information was present.

**Decision**: Split persona extraction into three stages: (1) post-processing via lightweight model to detect and filter taste signals, (2) persona building via primary model when new signals exist, (3) embedding. Stage 2 is conditionally skipped via a LangGraph conditional edge when no new signals are detected.

**Why**:
- Signal-based triggering avoids unnecessary persona rebuilds (cost savings, reduced latency).
- Using Haiku for post-processing and Sonnet for persona building optimizes cost/quality tradeoff.
- Separating signal detection from persona building lets each stage have a focused prompt.
- Graceful degradation at each stage: post-process fallback returns raw transcript, build-persona fallback returns current persona.

**Consequence**: Two Claude calls per turn (when signals exist) instead of one, but the Haiku call is cheap. Net code reduction of ~370 lines by removing heuristic keyword dictionaries.

---

## Design Decision: Portable Taste Profiles

**Context**: The persona was accumulating functional requirements (room dimensions, seating capacity, shape preferences) alongside aesthetic taste signals. Since the taste profile is intended to be reused across product categories and sessions, functional requirements polluted cross-context recommendations.

**Decision**: Both the post-process and persona-building prompts explicitly distinguish aesthetic taste signals from functional requirements. Only aesthetic signals (styles, materials, colors, textures, finishes, budget) flow into the persona. Functional requirements are filtered out.

**Why**:
- A taste profile saying "likes warm minimalism, oak, matte finishes" is portable across lighting, furniture, and decor.
- A taste profile saying "seats 4-6 people, square shape" is only relevant to one product search and corrupts recommendations for other categories.
- `budget_tier` is constrained to `"budget"`, `"mid"`, `"premium"`, or `null` to prevent raw signal leakage like "no limit".

**Consequence**: Functional requirements from the conversation are still available in the chat transcript for the discovery reply, but they don't persist into the taste profile.

---

## Design Decision: Graceful Degradation Over Failure

**Context**: The persona pipeline calls Claude twice per turn. Network failures, API rate limits, or malformed responses could break the chat flow.

**Decision**: Every Claude-dependent function in the persona pipeline accepts `client: AsyncAnthropic | None` and returns a deterministic fallback when the client is None or any exception occurs. The fallback never raises.

**Why**:
- The chat flow must remain operable during local development (no API key), partial outages, or malformed model output.
- Fallback behavior is explicit and testable: post-process returns raw transcript, build-persona returns current persona, discovery returns canned replies.

**Consequence**: Recommendation quality degrades without Anthropic, but the user flow never breaks. All fallback paths are covered by tests.

---

## Design Decision: Likes/Hates As Primary Embedding Signal

**Context**: The persona schema was simplified from 10 fields to 5 taste-focused fields. The recommendation embedding needed to capture the dominant taste signal.

**Decision**: `persona_to_text()` renders `likes` and `hates` first in the embedding text, making them the dominant CLIP embedding signal. Budget tier, approvals, and rejections follow.

**Why**:
- Taste descriptors like "warm and natural" carry more semantic weight for CLIP embeddings than individual product names.
- `likes`/`hates` accumulate from both conversation extraction and product feedback, creating a unified taste signal.

**Consequence**: Personas with only approvals/rejections (no taste keywords) produce weaker embeddings. This is acceptable because the pipeline progressively builds taste descriptors through conversation.

---

## Design Decision: Structured Discovery Reply With Suggestions

**Context**: Discovery replies were plain text strings. Suggestion bubbles needed to be generated alongside the reply.

**Decision**: Discovery nodes return `(content, suggestions)` tuples. Claude returns `{"reply": string, "suggestions": string[]}` JSON. The `suggestions` field flows through `AgentState`, an SSE event, and into the frontend `SuggestionBubbles` component.

**Why**:
- Co-generating reply + suggestions in one Claude call is cheaper and more contextually coherent than a separate call.
- Fallback suggestions are deterministic per persona completeness stage, so no API is needed for graceful degradation.

**Consequence**: All discovery reply paths (Claude, fallback, greeting) must produce both content and suggestions. The SSE event stream includes a `suggestions` event between `token` and `persona_update`.

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
def clear_sessions() -> None
def get_session_snapshot(session_id: str) -> SessionSnapshot
```

#### Session Snapshot Endpoint

```python
@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> SessionSnapshot
```

```python
class SessionMessage(CamelModel):
    role: Literal["user", "assistant"]
    content: str


class SessionSnapshot(CamelModel):
    session_id: str
    messages: list[SessionMessage]
    persona: Persona | None = None
    recommendations: list[Recommendation]
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
data: {"type": "suggestions", "suggestions": ["...", "...", "..."]}\n\n
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
  | { type: "suggestions"; suggestions: string[] }
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
| `GET /api/sessions/{sessionId}` | path param only | returns `SessionSnapshot` |

#### Response Contracts

| Endpoint | Response |
|----------|----------|
| Chat | SSE stream (see above) |
| Recommend | `Recommendation[]` with camelCase keys. Router uses `request.personaEmbedding` first, then falls back to session-backed `persona_embedding`, and returns `[]` if neither exists |
| Feedback | `{"persona": <camelCase Persona>}` |
| Session snapshot | `{"sessionId", "messages", "persona", "recommendations"}` with camelCase keys |

#### Session Persistence

- In-memory dict keyed by `session_id` (`app/services/session.py`)
- Chat endpoint loads previous state, appends user message, runs agent turn, saves result
- Feedback endpoint loads session, updates persona + embedding, saves back
- Session snapshot endpoint returns the current server-backed workspace state used by frontend hydration
- Missing sessions must return an empty snapshot payload instead of 404: `messages=[]`, `persona=null`, `recommendations=[]`
- Snapshot serialization must omit malformed message entries and only emit messages with `role in {"user", "assistant"}` plus string `content`
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
| No existing session for `sessionId` in snapshot endpoint | Return empty snapshot payload (200) | Router (session snapshot) |
| Stored session contains malformed message entries | Omit invalid items from `messages`, do not fail the response | Service -> Router |

### 5. Good / Base / Bad Cases

#### Good

- User sends 2+ messages, persona accumulates signals, recommend returns 6 products, feedback updates persona and persists to session.

#### Base

- First message in a new session: agent greets, persona is mostly empty, recommendations return empty (insufficient signals).

#### Bad

- Claude API is down: chat falls back to deterministic discovery reply + fallback persona pipeline, SSE stream still completes with `token` + `persona_update` + `done`.
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
- `tests/test_session_router.py`
  - Assert saved session state is returned as camelCase `sessionId`, `messages`, `persona`, and `recommendations`.
  - Assert missing sessions return an empty snapshot payload rather than 404.

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

- Why wrong: `model_dump()` without `by_alias=True` emits snake_case keys (`budget_tier`), but the frontend expects camelCase (`budgetTier`).

#### Correct

```python
yield _sse_event({"type": "persona_update", "persona": persona.model_dump(by_alias=True)})
```

#### Wrong

```python
session = get_session(session_id)
if session is None:
    raise NotFoundError(f"Session {session_id} not found")
```

- Why wrong: discovery-page restore treats session fetch as hydration, not an exceptional path. Missing sessions must hydrate to an empty workspace.

#### Correct

```python
if state is None:
    return SessionSnapshot(
        session_id=session_id,
        messages=[],
        persona=None,
        recommendations=[],
    )
```

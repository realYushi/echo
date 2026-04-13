# Journal - Yushi Cui (Part 1)

> AI development session journal
> Started: 2026-04-12

---



## Session 1: PR2: Product catalog + CLIP embeddings + Qdrant ingestion

**Date**: 2026-04-13
**Task**: PR2: Product catalog + CLIP embeddings + Qdrant ingestion
**Branch**: `main`

### Summary

(Add summary)

### Main Changes

## Implemented

| Component | Description |
|-----------|-------------|
| Seed data | 25 dummy products across 5 categories (furniture, bathroom, kitchen, lighting, building materials) |
| CLIP embeddings | `get_clip_embedding()` using open_clip ViT-B-32, lazy-loaded singleton, `asyncio.to_thread()` for async safety |
| Catalog service | `seed_catalog()` creates Qdrant collection (512-dim cosine), embeds all products, batch upserts with deterministic UUIDs |
| Recommendation service | `get_recommendations()` queries Qdrant with persona embedding, returns scored product list |
| Startup wiring | Catalog seeded automatically via lifespan context manager |

## Files Changed

- `backend/app/data/__init__.py` — new package
- `backend/app/data/products.py` — 25 seed products with rich descriptions
- `backend/app/utils/embeddings.py` — CLIP embedding with thread-safe lazy loading
- `backend/app/services/catalog.py` — Qdrant collection creation + product ingestion
- `backend/app/services/recommendation.py` — cosine similarity search + result mapping
- `backend/app/main.py` — seed_catalog wired into lifespan

## Testing

- All 25 products seeded into Qdrant on startup (~3.5s)
- Collection verified: green status, 25 points, 512-dim cosine
- Recommendation queries return semantically relevant results across 3 test queries
- Ruff lint + format: zero issues

## Next

PR3: LangGraph agent — 6-node graph + persona extraction + embedding + retrieval


### Git Commits

| Hash | Message |
|------|---------|
| `29be10a` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 2: Update backend specs with PR2 patterns

**Date**: 2026-04-13
**Task**: Update backend specs with PR2 patterns
**Branch**: `main`

### Summary

Updated 3 spec files: directory-structure.md (added app/data/), database-guidelines.md (real Qdrant patterns: idempotent collection creation, UUID5 point IDs, batch upsert, query_points API, common mistake), quality-guidelines.md (lazy singleton + asyncio.to_thread examples).

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `92847b3` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: PR3 review: LangGraph agent

**Date**: 2026-04-13
**Task**: PR3 review: LangGraph agent
**Branch**: `main`

### Summary

(Add summary)

### Main Changes

## What was done
- Reviewed PR3 (LangGraph agent) implemented by Codex
- 6-node graph: greet → discover → extract_persona → embed_persona → recommend → feedback
- Claude integration for conversation + persona extraction
- Persona JSON → embedding conversion + Qdrant retrieval
- InMemorySaver checkpointer (PostgreSQL deferred)

## Review Results
- All checks pass: ruff, mypy, pytest (5/5)
- 1 minor fix: removed redundant runtime import in `persona.py`
- Code quality: typed exceptions, type hints enforced, clean architecture

## Key Files
- `backend/app/agent/graph.py` — LangGraph graph wiring
- `backend/app/agent/nodes.py` — 6 node implementations
- `backend/app/agent/state.py` — agent state schema
- `backend/app/services/persona.py` — persona extraction + embedding
- `backend/tests/test_agent_graph.py` — graph tests
- `backend/tests/test_persona.py` — persona tests
- `.trellis/spec/backend/agent-recommendation-flow.md` — spec added

## Notes
- InMemorySaver means sessions don't survive restarts (known, spec-acknowledged)
- `apply_feedback()` adds style tags from disliked products — potential drift, matches spec
- Updated task.json: status → in-progress, PR1/PR2 subtasks → done

## Next
- PR4: API layer (SSE streaming, chat/recommend/feedback endpoints) — Codex to implement


### Git Commits

| Hash | Message |
|------|---------|
| `adde887` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 4: PR4: API layer — SSE chat, recommend, feedback endpoints

**Date**: 2026-04-14
**Task**: PR4: API layer — SSE chat, recommend, feedback endpoints
**Branch**: `main`

### Summary

(Add summary)

### Main Changes


## Implemented

| Component | Description |
|-----------|-------------|
| CamelModel base | `app/schemas/base.py` — shared Pydantic base with `alias_generator=to_camel` for camelCase API serialization |
| Chat endpoint | `POST /api/chat` — SSE streaming via `run_agent_turn()`, emits `token`, `persona_update`, `done`, `error` events |
| Recommend endpoint | `POST /api/recommend` — accepts `personaEmbedding`, queries Qdrant via `get_recommendations()`, returns camelCase JSON |
| Feedback endpoint | `POST /api/feedback` — looks up product, calls `apply_feedback()`, re-embeds persona, updates session store |
| Session store | `app/services/session.py` — in-memory dict for cross-turn agent state persistence |
| Schema updates | `ChatRequest` (sessionId + message + persona), `RecommendRequest` (sessionId + personaEmbedding), `FeedbackRequest` (+sessionId) |

## Key Learnings

- FastAPI + `from __future__ import annotations` + `TYPE_CHECKING` = broken schema generation. Endpoint signature types must be imported at runtime with `# noqa: TC001/TC002`.
- `model_dump(by_alias=True)` is required for manual serialization (SSE events, dict returns). FastAPI auto-serializes by alias for Pydantic response models.
- SSE error handling is the one exception to "services raise, routers don't catch" — stream must always emit `done` event.

## Files Changed

- `backend/app/schemas/base.py` — new CamelModel base
- `backend/app/schemas/chat.py` — updated ChatRequest (message + persona)
- `backend/app/schemas/persona.py` — inherits CamelModel
- `backend/app/schemas/product.py` — inherits CamelModel, added RecommendRequest + sessionId
- `backend/app/services/session.py` — new in-memory session store
- `backend/app/services/persona.py` — minor formatting
- `backend/app/routers/chat.py` — real SSE streaming with DI
- `backend/app/routers/recommend.py` — real Qdrant retrieval with DI
- `backend/app/routers/feedback.py` — real feedback with DI + session update
- `.trellis/spec/backend/agent-recommendation-flow.md` — API layer contract scenario
- `.trellis/spec/backend/directory-structure.md` — updated layout + runtime import docs
- `.trellis/spec/backend/error-handling.md` — SSE error pattern
- `.trellis/spec/backend/quality-guidelines.md` — CamelModel + TC gotcha
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — camelCase + TYPE_CHECKING mistakes

## Testing

- ruff: 0 issues
- mypy strict: 0 issues
- pytest: 5/5 passing
- Manual E2E: chat (2-turn session), recommend (6 results), feedback (like + dislike), error handling (404, empty embedding)

## Next

PR5: Frontend — split-pane discovery UI + streaming chat + recommendation grid + feedback buttons


### Git Commits

| Hash | Message |
|------|---------|
| `b1fd5ac` | (see git log) |
| `53652d1` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete

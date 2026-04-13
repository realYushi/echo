# MVP: Product Recommendation via Guided Chatbot

## Goal

Build a thin-production-stack MVP proving the elimination-first discovery loop end-to-end for a high-end architecture/home solutions e-commerce platform. Homeowners describe what they want by reacting to what they see — rejecting, approving, refining in natural language. The system builds a taste profile from these reactions and surfaces products the customer didn't know existed but immediately recognizes as right.

Solo founder, AI-assisted development. Not a throwaway demo — real architecture, dummy data.

## Requirements

- User clicks Discover → split-pane UI opens (chat left, recommendations right)
- Chatbot conducts elimination-first discovery conversation (rejection is the primary signal)
- Persona JSON extracted after each exchange via Claude, converted to embedding
- Recommendations retrieved from Qdrant via persona embedding cosine similarity
- Recommendations update live as persona evolves through conversation
- "More like this" / "Not for me" buttons on product cards steer persona
- Session persists across browser refreshes via LangGraph checkpoints
- Graceful fallback if Claude API fails mid-conversation

## Acceptance Criteria

- [ ] User clicks Discover → split-pane opens
- [ ] Chatbot asks about project context in opening messages
- [ ] Persona JSON populated after each exchange
- [ ] Persona embedding generated and queryable in Qdrant
- [ ] Recommendations appear once persona has ≥2 signals
- [ ] Feedback buttons visibly change next recommendation set
- [ ] Empty state shown when no products match persona
- [ ] API error shows graceful fallback message, chat remains usable
- [ ] Session resumes after page refresh

## Definition of Done

- TypeScript strict, no `any` types (frontend)
- Python type hints enforced (backend)
- Lint / typecheck pass
- Core flow works end-to-end (button → chat → persona → recommendations → feedback)
- No hardcoded test data in production paths

## Technical Approach

- **Frontend**: Next.js (App Router), TypeScript, React
- **Backend**: Python, FastAPI
- **Vector DB**: Qdrant (Docker for local dev)
- **LLM Orchestration**: LangGraph (stateful agent graph)
- **LLM**: Claude Sonnet for conversation + persona extraction
- **Embeddings**: CLIP/OpenCLIP multimodal (text + image) for product catalog
- **Persona Model**: Hybrid — LLM-extracted structured JSON + persona embedding for Qdrant retrieval
- **Agent Graph**: Modular 6-node graph — `greet → discover → extract_persona → embed_persona → recommend → feedback`
- **Catalog**: Static JSON seed (~25 dummy products across furniture, bathroom, kitchen, lighting, building materials)
- **Persistence**: LangGraph checkpoints in PostgreSQL
- **Streaming**: SSE for LLM token streaming
- **Layout**: Desktop split-pane — chat left, live recommendations right

### Persona Schema

```json
{
  "projectType": "string | null",
  "budgetTier": "string | null",
  "role": "string | null",
  "stylePreferences": ["string"],
  "materialPreferences": ["string"],
  "categories": ["string"],
  "rejections": ["string"],
  "approvals": ["string"]
}
```

### Product Schema

```json
{
  "id": "string",
  "name": "string",
  "category": "string",
  "subcategory": "string",
  "tags": ["string"],
  "budgetTier": "string",
  "imageUrl": "string",
  "description": "string"
}
```

### API Surface

- `POST /api/chat` — messages + current persona → streamed response + updated persona (SSE)
- `POST /api/recommend` — persona embedding → scored product list from Qdrant
- `POST /api/feedback` — product ID + signal (like/dislike) → updated persona

## Decision (ADR-lite)

**Context**: Greenfield MVP, solo founder with AI-assisted dev. Need to prove elimination-first discovery loop without throwaway code. Full PRD envisions LangGraph + Qdrant + CLIP + Kafka + Feature Store for a team of 4-6 — too heavy for solo MVP.

**Decision**: Thin production stack — Next.js + FastAPI + Qdrant + LangGraph. Skip Kafka, feature store, multi-stage ranking funnel, and MLOps. Hybrid persona model (structured JSON + embedding) for both debuggability and real vector retrieval. Multimodal CLIP embeddings for product catalog because visual similarity is essential for home/architecture products.

**Consequences**: Architecture is real and extensible — no rewrite needed to add Kafka, behavioral signals, or multi-faceted personas later. Single-stage ANN retrieval (no ranking/re-ranking) is acceptable for ~25 products. Persona drift from single-facet vector is a known limitation (multi-facet is Phase 3).

## Implementation Plan

| PR | What | Key Deliverables |
|---|---|---|
| PR1 | Scaffolding | Next.js + FastAPI + Qdrant (Docker) + PostgreSQL + project structure |
| PR2 | Product catalog | ~25 dummy products with images, CLIP embedding pipeline, Qdrant ingestion |
| PR3 | LangGraph agent | 6-node graph, Claude integration, persona extraction + embedding, Qdrant retrieval, checkpoints |
| PR4 | API layer | SSE streaming, chat endpoint, recommend endpoint, feedback endpoint |
| PR5 | Frontend | Split-pane discovery UI, streaming chat, recommendation grid, feedback buttons, empty/error states |
| PR6 | Integration + polish | End-to-end wiring, session resume, graceful degradation |

## Out of Scope

- Kafka / event streaming
- Feature store
- Multi-stage ranking funnel (retrieval → ranking → re-ranking)
- Multi-faceted personas (per room/context)
- Behavioral signals (scroll, dwell, zoom)
- Taste profile bar UI
- Admin dashboard / session replay
- User auth, payments, cart
- Mobile optimization
- MLOps / automated retraining
- A/B testing framework
- CDC pipeline for real catalog sync
- Voice interaction

## Technical Notes

- Full vision PRD: `plans/_bmad-output/planning-artifacts/prd.md`
- Technical research: `plans/_bmad-output/planning-artifacts/research/technical-ai-recommendation-engine-research-2026-04-12.md`
- Brainstorm session: `plans/_bmad-output/brainstorming/brainstorming-session-2026-04-12-001.md`
- Product categories: furniture, bathroom solutions, kitchen fixtures, lighting, building materials
- LLM cost per session estimated at $0.02–0.10 for 10–15 exchanges
- Qdrant Cloud free tier or Docker for local dev

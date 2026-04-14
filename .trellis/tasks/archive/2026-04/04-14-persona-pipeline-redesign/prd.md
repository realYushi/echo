# Redesign Persona Building with Post-Processing Pipeline

## Goal

Decouple persona extraction from the chat loop by introducing a lightweight post-processing step between conversation and persona building. This creates three logical stages — chat, post-processing, and persona building — where the post-processor both filters conversation noise and acts as a signal-based trigger gate for persona rebuilds. Simplify the persona schema to focus on taste.

## Requirements

* **Three-stage pipeline**:
  1. **Chat thread** — Sonnet handles discovery conversation, generates replies + suggestions (largely unchanged)
  2. **Post-processor** — lightweight model (Haiku-class) receives recent messages, filters out noise/small-talk, extracts taste-relevant signals, and decides whether a persona rebuild is warranted
  3. **Persona builder** — receives filtered signals + current persona + JSON schema; model outputs updated persona directly (schema-guided, not heavy programmatic construction)

* **Signal-based triggering**: Post-processor determines whether new messages contain meaningful taste signals. If no new signal detected, skip persona rebuild. Always trigger when persona is empty or below a minimum signal threshold.

* **Simplified persona schema** (taste-focused):
  - `budget_tier`: str | None — hard filter for recommendations (budget / mid / premium)
  - `likes`: list[str] — positive taste signals (styles, materials, vibes, aesthetic preferences)
  - `hates`: list[str] — negative taste signals
  - `approvals`: list[str] — specific products the user liked
  - `rejections`: list[str] — specific products the user rejected

* **Dropped fields**: `project_type`, `role`, `categories`, `style_preferences`, `material_preferences`
  - `style_preferences` and `material_preferences` merge into `likes`/`hates`
  - `categories` dropped entirely — user manually selects category in recommendation UI
  - `project_type` and `role` dropped — don't meaningfully drive taste-based recommendations

* **Schema-guided persona building**: Give the model the JSON schema + clear instructions and let it handle structured output. Minimal programmatic post-processing (validation only, not correction). The current heuristic extraction and normalization pipeline can be greatly simplified or removed.

* **Product feedback path**: Keep existing feedback flow (like/dislike on products → approvals/rejections) as-is for now. Does not route through post-processor. Will be revisited in a follow-up task.

## Acceptance Criteria

* [ ] Chat → post-process → persona build pipeline is functional end-to-end
* [ ] Post-processor correctly identifies messages with taste signals vs. noise
* [ ] Post-processor skips persona rebuild when no new signals detected
* [ ] Post-processor always triggers rebuild when persona is empty/minimal
* [ ] Persona schema reduced to 5 fields (budget_tier, likes, hates, approvals, rejections)
* [ ] Persona builder uses model + JSON schema to produce valid output
* [ ] Frontend updated to handle simplified persona schema
* [ ] Existing product feedback flow (like/dislike) still works
* [ ] Embedding generation works with simplified persona text

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes

## Out of Scope (explicit)

* Category-based recommendation filtering (user manually selects)
* Redesigning the product feedback pipeline
* Recommendation retrieval changes (stays as pure vector similarity)
* Further persona schema polishing (follow-up task)
* Cross-category recommendation support

## Decision (ADR-lite)

**Context**: Current `extract_persona` runs after every message, sends the full transcript to Sonnet, and returns a 10-field JSON that then gets programmatically normalized. This is expensive, noisy, and tightly coupled.

**Decision**: Split into three stages with a lightweight post-processor as signal gate. Simplify persona to 5 taste-focused fields. Let the model handle structured output via schema rather than heavy heuristic correction.

**Consequences**:
- Cheaper per-turn cost (Haiku for filtering, Sonnet only when signals detected)
- Cleaner separation of concerns
- Simpler persona schema = cleaner embeddings = potentially better recommendations
- Heuristic fallback path (`_heuristic_persona`, `_normalize_persona_signals`) becomes largely obsolete — can be removed or reduced to minimal validation
- Frontend needs schema migration (10 fields → 5)

## Technical Notes

* Key files to modify:
  - `backend/app/services/persona.py` (604 lines) — extraction logic, largely rewritten
  - `backend/app/agent/graph.py` — pipeline node structure
  - `backend/app/agent/nodes.py` — node implementations
  - `backend/app/schemas/persona.py` — schema simplification
  - `frontend/src/types/persona.ts` — Zod schema update
  - `frontend/src/hooks/usePersona.ts` — state management update
* Spec: `.trellis/spec/backend/agent-recommendation-flow.md` — needs update
* `persona_to_text()` becomes simpler with fewer fields and cleaner taste focus
* LangGraph pipeline may need a conditional edge (post-processor → skip or → persona build)

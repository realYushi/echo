# Expand "Taste profile" panel into full conversation-state view

## Goal

Replace the minimal right-sidebar "Taste profile" section in `frontend/src/app/discover/page.tsx` with an expanded inspector that surfaces **everything the system knows about the live conversation** — persona signals, recommendations, chat state — organized into **collapsible sections** the user can toggle open/closed while debugging or demoing.

## What I already know (from repo inspection)

- The page lives at `frontend/src/app/discover/page.tsx` (title shown as "Taste profile", likely what the user called "test profile").
- Current taste-profile card (lines 255–324) only renders three facets: `budgetTier`, `likes`, `hates`. It ignores other known persona fields.
- Full `Persona` schema (`frontend/src/types/persona.ts`, `backend/app/schemas/persona.py`) exposes:
  - `budgetTier` (string | null)
  - `likes` (string[])
  - `hates` (string[])
  - `approvals` (string[] — product IDs the user thumbed up)
  - `rejections` (string[] — product IDs the user thumbed down)
- `SessionSnapshot` (`frontend/src/types/session.ts`) also carries `messages` and `recommendations` (each with a `score`).
- Agent state (`backend/app/agent/state.py`) holds more internals but is not currently exposed to the client (persona_embedding, suggestions, pending_feedback, has_new_signals, filtered_signals).
- Chat hook (`frontend/src/hooks/useChat.ts`) locally tracks `messages`, `suggestions`, `isStreaming`, `error`.
- No `<Collapsible>` / `<Accordion>` primitive exists yet under `frontend/src/components/ui/`.

## Assumptions (to validate)

- "Test profile" = the right-sidebar "Taste profile" panel (word slip — the page has no separate test/debug view).
- All info should come from data **already available on the client** (no new backend endpoints).

## Decisions so far

- **Audience (Q1)**: Both. Default view stays polished and user-facing; a "Developer mode" toggle reveals a raw inspector on top of the polished sections. (Picked 2026-04-17.)
- **Sections (Q2)**: Ship full list A–K. (Picked 2026-04-17.)
  - **Polished (always visible)**:
    - A. Budget & direction (`budgetTier` + chips)
    - B. Likes (`persona.likes`)
    - C. Dislikes (`persona.hates`)
    - D. Approved products (resolve `persona.approvals` IDs → product names)
    - E. Rejected products (resolve `persona.rejections` IDs → product names)
    - F. Session summary (session id, message count, streaming/loading state)
  - **Developer view (behind toggle)**:
    - G. Raw persona JSON (pretty-printed)
    - H. Recommendations with scores (product id + score)
    - I. Assistant suggestions (`chat.suggestions`)
    - J. Live chat state (`isStreaming`, `error`, last message role)
    - K. Raw session snapshot JSON
- **UX defaults (Q3)**: Dev-mode toggle persists via `localStorage`. Section open/closed state defaults collapsed on first load and is remembered only within the current tab session (in-memory React state). (Picked 2026-04-17.)

## Technical Approach

- Add a tiny `CollapsibleSection` primitive under `frontend/src/components/ui/` (chevron + Tailwind-styled `<button>` + conditional body). Prefer this over native `<details>` for consistent styling with the surrounding card.
- Extract the current right-sidebar taste card into a new component `frontend/src/components/profile/ProfileInspector.tsx`. Inputs: `persona`, `recommendations`, `chatState` (messages, suggestions, isStreaming, error), `sessionId`, `isHydrating`.
- Inspector owns:
  - `devMode` boolean, persisted to `localStorage` under a namespaced key (e.g. `echo:profile-inspector:devMode`).
  - A `Record<sectionId, boolean>` of open/closed state (in-memory `useState`; all default `false`).
- Resolve approval/rejection product IDs via the already-loaded `recommendations` list on the client; fall back to showing the raw ID if unknown (no new API needed).
- Keep the rest of `DiscoverPage` unchanged (layout, voice, hydration flow).

## Final Requirements

- Right-sidebar panel renders all 5 persona fields (A–E) + session summary (F) as independently collapsible sections, all collapsed by default.
- A "Developer mode" toggle at the top of the panel adds sections G–K below the polished ones; toggle state persists in `localStorage`.
- Approved/rejected sections resolve product IDs to names where possible using client-side recommendations data.
- Works identically in text and voice modes.
- No backend changes.

## Acceptance Criteria

- [ ] All five persona fields render with their own collapsible section; clicking a header toggles just that section.
- [ ] Sections start collapsed; expanded state persists while switching between text/voice and between sessions in the same tab.
- [ ] "Developer mode" toggle reveals sections G–K; state survives a page reload.
- [ ] Session summary shows session id (truncated), message count, and a live hydrating/streaming indicator.
- [ ] Dev-mode raw JSON blocks are readable (monospace, scrollable for long content).
- [ ] `npm run lint` and `npm run typecheck` pass.

## Out of Scope

- New backend endpoints or exposing additional agent internals (persona_embedding, pending_feedback, filtered_signals) — use only data already on the client.
- Persisting section open/closed state across reloads.
- Reworking the overall page layout.

## Implementation Plan (single PR)

1. Add `CollapsibleSection` UI primitive + unit test.
2. Add `ProfileInspector` component with polished sections A–F.
3. Add developer mode toggle + sections G–K, wire `localStorage`.
4. Replace the inline taste-profile section in `DiscoverPage` with `<ProfileInspector />`.
5. Lint + typecheck + smoke test in both text and voice modes.

## Requirements (evolving)

- Expand the right-sidebar "Taste profile" section to show all persona fields, not just three.
- Organize content into collapsible sections the user can independently toggle.
- Keep working during both text and voice modes.

## Acceptance Criteria (evolving)

- [ ] All five persona fields render (budgetTier, likes, hates, approvals, rejections).
- [ ] Sections are individually foldable (open/close state preserved while navigating).
- [ ] Page keeps building cleanly (lint + typecheck pass).

## Definition of Done

- Tests updated where behavior changed
- Lint / typecheck / CI green
- No regressions on voice mode or session hydration

## Out of Scope (tentative)

- Backend changes (new endpoints, exposing agent internals not already shipped).
- Persisting the open/close state across sessions.

## Technical Notes

- Relevant files: `frontend/src/app/discover/page.tsx` (lines 255–324), `frontend/src/types/persona.ts`, `frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useRecommendations.ts`.
- No existing accordion/collapsible primitive — will need to either add one under `frontend/src/components/ui/` or use native `<details>/<summary>`.
- Tailwind v4 + React 19 + strict TS in use.

# MVP: Product Recommendation via Guided Chatbot

## Goal

Build a small MVP for a high-end architecture/design platform (architects, designers, homeowners). Customer clicks "Discover" → chatbot guides discovery conversation → persona built in background → split-pane recommendations appear live as conversation progresses → feedback refines results.

## Requirements

- "Discover" button triggers split-pane UI (chat left, recommendations right)
- Chatbot opens with 2 anchor questions: project type (new build / renovation) + budget tier
- Chatbot continues conversation to extract style, material, category preferences
- Persona object updated after each message (background, not visible to user)
- Recommendations populate right pane live as persona confidence grows
- "More like this" / "Not for me" buttons on each card → re-ranks recommendations
- Two product categories in catalog:
  1. Physical goods — furniture, bathroom solutions, in-house products
  2. Design solutions — roofing, electrical design, building suppliers, car parts
- Empty state when no products match persona
- Graceful error state if Claude API fails mid-conversation

## Acceptance Criteria

- [ ] User clicks Discover → split-pane opens
- [ ] Chatbot asks project type and budget tier in first 2 messages
- [ ] Persona object is populated after each chatbot exchange
- [ ] Recommendations appear in right pane once persona has ≥2 signals
- [ ] "More like this" steers toward that product type; "Not for me" removes that type
- [ ] Empty state shown when catalog has no matches
- [ ] API error shows graceful fallback message, chat remains usable

## Definition of Done

- TypeScript strict, no `any` types
- Lint / typecheck pass
- Core flow works end-to-end (button → chat → recommendations → feedback)
- No hardcoded test data in production paths

## Technical Approach

- **Stack**: Next.js (App Router), TypeScript, React
- **LLM**: Claude API — `claude-sonnet-4-6` for chat + persona extraction
- **Persona**: Extracted via structured JSON response after each message. Fields: `projectType`, `budgetTier`, `role`, `stylePreferences`, `materialPreferences`, `categories`
- **Catalog**: Static JSON seed (~25 products across furniture, bathroom, roofing, electrical, building supply)
- **Recommendation logic**: Client-side scoring — match persona fields against product tags, re-score on feedback
- **Layout**: Split pane — chat left, live recommendations right

## Decision (ADR-lite)

**Context**: Greenfield MVP, need fast iteration, high-end UX bar.
**Decision**: Next.js full-stack (API routes for LLM calls), static JSON catalog, client-side re-ranking.
**Consequences**: No backend infra to manage. Real catalog swap = replace JSON + scoring logic. Persona is session-only (no persistence).

## Out of Scope

- User accounts / authentication
- Payment / cart integration
- Admin dashboard / catalog management
- Analytics / tracking
- Saved personas across sessions
- Collaborative sessions (architect + client)
- Real product catalog integration

## Technical Notes

- API route: `POST /api/chat` — takes messages + current persona, returns next message + updated persona
- API route: `POST /api/recommend` — takes persona, returns scored product list
- Product schema: `{ id, name, category, subcategory, tags[], budgetTier, imageUrl, description }`
- Persona schema: `{ projectType, budgetTier, role, stylePreferences[], materialPreferences[], categories[] }`
- Single repo, Vercel-compatible deployment

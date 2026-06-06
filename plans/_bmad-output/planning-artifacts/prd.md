---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments:
  - 'prfaq-prd.md'
  - 'prfaq-prd-distillate.md'
  - 'research/technical-ai-recommendation-engine-research-2026-04-12.md'
  - '_bmad-output/brainstorming/brainstorming-session-2026-04-12-001.md'
workflowType: 'prd'
documentCounts:
  briefs: 0
  research: 1
  prfaq: 2
  brainstorming: 1
  projectDocs: 0
classification:
  projectType: 'web_app'
  domain: 'e-commerce'
  complexity: 'high'
  projectContext: 'greenfield-on-brownfield'
---

# Product Requirements Document - Echo

**Author:** Yushi
**Date:** 2026-04-12

## Executive Summary

Echo is an AI-powered discovery engine that replaces keyword search with elimination-first conversation on an existing architecture and home solutions e-commerce platform. Homeowners furnishing or renovating spaces — especially first-timers who have taste but lack design vocabulary — describe what they want by reacting to what they see: rejecting, approving, and refining in natural language. The system builds a multi-faceted taste profile from these reactions, and that profile drives product recommendations across every category on the platform — furniture, fixtures, lighting, building materials, and design services.

The core thesis: customers cannot articulate preferences in design language, but they can instantly recognize what's right and what's wrong. Echo exploits that asymmetry. Within 90 seconds, the AI builds a working taste profile from rejection signals and conversational context, then surfaces products the customer didn't know existed but immediately recognizes as right. The profile sharpens with every visit, remembers that taste differs room by room, and becomes the primary reason to return.

Echo launches as an enhancement layer on a production platform with existing customers, catalog, and commerce infrastructure. If the AI underperforms, the platform continues operating — customers browse, search, and buy exactly as they do today. This is not a standalone AI pilot; it is a measurable improvement on a working baseline.

### What Makes This Special

**Elimination-first discovery.** Rejection is the primary signal, not selection. "Too bulky" or "not warm enough" teaches the system more than a five-star review. This is grounded in cognitive science — it's easier to say "not that" than to articulate "exactly this" — and no competitor in the home products space uses this approach.

**Conversation is the search.** The chat agent and recommendation engine operate in the same vector space. Each message, swipe, and reaction mathematically adjusts the persona vector that drives product retrieval. There is no handoff between "talking to the AI" and "getting results" — they are a single operation.

**Taste profile as switching cost.** After six months of multi-faceted preferences across five rooms — bold color in the living room, natural materials in the kitchen, no chrome anywhere — leaving Echo means starting over from scratch on any other platform. The accumulated taste profile is the durable moat, not the technology stack.

**Enhancement, not replacement.** The existing platform provides the customer base, catalog, payments, shipping, and returns. Echo adds an AI discovery layer with graceful degradation. Any measurable improvement over the baseline is a win, eliminating the all-or-nothing risk that kills 87% of AI pilots.

## Project Classification

- **Project Type:** Web application — real-time conversational UI with streaming LLM responses, swipe-based interactions, and live recommendation updates
- **Domain:** E-commerce — mid-to-high-end architecture and home solutions (furniture, kitchen/bath fixtures, lighting, building materials, electrical, design services)
- **Complexity:** High — novel AI/ML system combining multimodal embedding pipelines, real-time persona modeling, stateful LLM agent orchestration (LangGraph), multi-stage recommendation funnel, event-driven microservices, and GDPR/privacy considerations
- **Project Context:** Greenfield AI feature on brownfield e-commerce platform — new discovery engine built on existing production infrastructure with existing customers and catalog

## Success Criteria

### User Success

- **Speed-to-value:** First relevant recommendation within 90 seconds of starting a discovery conversation
- **Recognition moment:** Users identify products they didn't know existed but immediately recognize as right — measured by click-through rate on recommendations surfaced after the third exchange
- **Elimination fluency:** Users can refine recommendations through natural rejection language ("too bulky," "not warm enough") without needing design vocabulary
- **Cross-category coherence:** Taste profile spans product categories so that kitchen and living room recommendations feel like they belong in the same home
- **Return recognition:** Returning users experience continuity — Echo resumes from their existing taste profile without re-discovery

### Business Success

- **Conversion rate uplift:** Echo-assisted sessions convert >10% higher than unassisted baseline (Phase 2), >30% (Phase 4)
- **Engagement lift:** Echo-assisted session engagement time >3 minutes (Phase 2), >8 minutes (Phase 4)
- **Recommendation CTR:** >5% (Phase 2), >15% (Phase 4)
- **Return user rate (30-day):** >20% (Phase 2), >40% (Phase 4) — to be validated against platform baseline
- **Revenue model validation:** Transaction revenue from Echo-assisted purchases exceeds AI infrastructure cost per session by at least an order of magnitude
- **Baseline comparison:** Every metric measured against the existing unassisted platform experience — any measurable improvement is net positive, targets above are stretch goals

### Technical Success

- **Recommendation latency (non-LLM path):** < 100ms P99 end-to-end (retrieval + ranking + re-ranking)
- **LLM streaming:** First token < 500ms, full response streamed < 2 seconds
- **Embedding quality (MVP bar):** Product embeddings correctly cluster by functional category (dining tables separate from coffee tables, kitchen faucets separate from bathroom faucets) and by dominant style signal (modern vs. traditional within category)
- **System availability:** > 99.9% uptime
- **Graceful degradation:** If AI layer fails, platform falls back to current browsing experience with zero customer-facing errors
- **Embedding freshness:** New products searchable within 15 minutes of catalog entry (post-MVP, when using real catalog)

### Measurable Outcomes

| Metric | Phase 2 (MVP) | Phase 4 (Scale) | How Measured |
|---|---|---|---|
| Time to first relevant recommendation | < 90 seconds | < 60 seconds | Session timer from first message to first recommendation click |
| Recommendation CTR | > 5% | > 15% | Clicks on Echo recommendations / recommendations served |
| Conversion uplift vs. baseline | > 10% | > 30% | A/B test: Echo-assisted vs. unassisted sessions |
| Session engagement time | > 3 min | > 8 min | Average active session duration |
| 30-day return rate | > 20% | > 40% | Unique users returning within 30 days |
| Persona completeness after 1 session | > 30% | > 50% | Taste profile vector coverage across active facets |
| Non-LLM recommendation latency (P99) | < 100ms | < 100ms | Server-side instrumentation |

## User Journeys

### Journey 1: Sarah Discovers Her Kitchen Style (First-Time Homeowner — Success Path)

Sarah and her partner closed on a 1960s ranch house three weeks ago. The kitchen needs everything — cabinets, countertops, a faucet, lighting, flooring. She's spent hours on Houzz and Amazon opening dozens of tabs, but she can't name what she likes. She knows the all-white farmhouse look isn't her, and she hates the industrial loft aesthetic her partner keeps suggesting. But when someone asks "what style do you want?" she freezes.

She finds Echo on the platform she already uses for building materials. Instead of a search box, there's a conversation. "What are you working on?" the AI asks. She types: "Kitchen renovation, full gut." Echo shows her six kitchen scenes. She swipes past the first three immediately — too cold, too busy, too shiny. She taps on one with warm wood and matte black hardware. "I like this feeling but the countertop is wrong," she types. Echo adjusts instantly.

By the fourth round — less than 90 seconds in — recommendations start landing closer. Echo shows her a brushed brass faucet she's never seen before. She didn't search for it. She couldn't have described it. But it's exactly right. She taps it, adds it to her project, and keeps going. Twenty minutes later she has a faucet, pendant lights, and cabinet hardware that all feel like they belong together — because they were all selected by the same taste profile.

She comes back two days later to look at countertops. Echo remembers everything. No re-discovery. It already knows she rejected every polished chrome fixture, gravitates toward natural materials, and prefers warm over cool tones. The countertop recommendations start from that foundation, not from zero.

**Critical moment:** The brushed brass faucet — the product she couldn't have searched for but immediately recognized as right.

**Failure scenario:** If the first four rounds show products that feel random or repetitive, Sarah closes the tab and goes back to scrolling Houzz. Speed-to-value is existential — the system has 90 seconds to prove it understands her, or she's gone.

### Journey 2: Sarah's Living Room Contradicts Her Kitchen (Edge Case — Conflicting Taste)

Two months after her kitchen renovation, Sarah returns to furnish her living room. Her kitchen taste was warm, natural, restrained. But for the living room she wants something bolder — jewel tones, a statement sofa, maybe a rug with personality. She's a different person in this room.

In MVP (single-facet persona), Echo's first living room recommendations lean toward the warm-minimal palette it learned from her kitchen. Sarah rejects several. "These are too safe — I want more color." Echo recalibrates from the rejection signals, but the single persona vector is now a blend of kitchen restraint and living room boldness. Kitchen recommendations, if she checked, would have drifted slightly.

This journey exposes the need for multi-faceted personas (Phase 3). The taste profile must understand that kitchen-Sarah and living-room-Sarah have different vectors. For MVP, the workaround is acceptable — rejection signals will eventually push the persona toward the right living room recommendations, just slower and with some kitchen drift.

**Critical moment:** When Sarah says "these are too safe" and Echo adjusts. Even without multi-facet, the rejection loop must respond visibly to explicit feedback within the same session.

**Failure scenario:** Echo keeps showing warm-minimal living room products because the kitchen persona is too strong. Sarah feels the system is stuck and stops trusting it.

### Journey 3: Mark Browses Without a Project (Returning Homeowner — Low Intent)

Mark used Echo six months ago to furnish his apartment. He's not renovating anything — he's just browsing on a Saturday morning with coffee. He opens the platform and Echo greets him by name with his existing profile.

Echo shows him new arrivals filtered through his taste profile. A floor lamp catches his eye — it's the kind of thing he'd never search for, but Echo knows he likes warm lighting and mid-century shapes. He taps it, reads the details, but doesn't buy. He spends eight minutes browsing, saves two items, and leaves.

From Echo's perspective, this session is high value even without a purchase. Mark's browsing behavior refines his persona further. His return validates the taste profile as a retention mechanism. The two saved items are warm leads for a future conversion.

**Critical moment:** The personalized greeting and immediately relevant new arrivals. Mark didn't come with intent — Echo created intent by showing him something he didn't know he wanted.

**Failure scenario:** Echo shows Mark generic "trending" products that don't reflect his profile. He sees no difference from any other e-commerce site and doesn't return.

### Journey 4: Yushi Monitors Echo's Performance (Admin/Operations — Solo Founder)

Yushi deploys the MVP with dummy product data and invites 15 beta testers. He needs to understand whether the discovery loop is working — are recommendations improving with each rejection? Are users engaging past the first 90 seconds? Is the embedding quality good enough?

He checks a lightweight dashboard: session count, average exchanges per session, recommendation CTR, and a log of persona vector changes per session. He picks one tester's session and replays it: first recommendation set was scattered (expected — thin persona), but by the fifth exchange the recommendations clustered around warm contemporary. The persona vector moved meaningfully with each rejection. The loop is working.

He notices one tester's session where every recommendation was rejected for 12 straight rounds. He digs into the embedding space and discovers the dummy catalog has only 3 products in the "modern rustic" cluster — not enough variety for the system to find a match. He flags the category gap and adds more dummy products in that cluster.

**Critical moment:** The ability to replay a session and see how the persona vector evolved with each interaction. Without this observability, Yushi can't distinguish "the algorithm is bad" from "the catalog is thin."

**Failure scenario:** Yushi has no visibility into why recommendations are failing — can't diagnose whether it's an embedding quality problem, a catalog coverage problem, or a conversation design problem.

### Journey 5: Architect Laura Evaluates Echo for Client Work (Future User — Validates the Cut)

Laura is an interior architect who manages 4-5 residential projects simultaneously. She uses the platform today for sourcing building materials and fixtures. She discovers Echo and immediately sees potential — instead of manually curating mood boards for each client, she could use Echo to rapidly surface options that match a client's taste profile.

But Echo's MVP doesn't support her workflow. She needs separate taste profiles per client, shareable recommendation sets, project-level organization, and persona seeding from external input. None of this exists in v1.

Laura bookmarks Echo and returns to her current workflow. Her journey validates that the architect persona is a genuine expansion opportunity but correctly deferred from MVP. The consumer discovery loop must prove itself first.

**What this journey tells us:** When the time comes, the requirements are: multi-client profiles, shareable recommendation sets, project organization, and persona seeding from external input.

### Journey Requirements Summary

| Journey | Key Capabilities Revealed |
|---|---|
| Sarah's Kitchen (success path) | Conversational discovery UI, elimination-first interaction, real-time persona building, cross-category recommendations, session persistence |
| Sarah's Living Room (edge case) | Persona recalibration from explicit feedback, single-facet limitation awareness, need for multi-faceted personas (Phase 3) |
| Mark Browsing (returning user) | Taste profile persistence across sessions, personalized new arrival surfacing, low-intent engagement value, behavioral signal capture |
| Yushi Monitoring (admin) | Session replay, persona vector visualization, embedding cluster analysis, recommendation quality metrics, catalog gap detection |
| Architect Laura (future user) | Multi-client profiles, shareable recommendations, project organization — validates Phase 4 scope and confirms the v1 cut |

## Domain-Specific Requirements

### Compliance & Regulatory

**GDPR / Data Privacy:**
- Existing platform handles GDPR consent, cookie consent, and data deletion infrastructure — Echo extends this for taste profile data specifically
- Taste profiles are personal data: consent required at account creation, disclosed in privacy policy
- Right to portability: taste profile exportable in machine-readable format (Phase 4 feature, but data architecture must support it from Day 1)
- Right to erasure: account deletion purges all persona vectors, conversation history, and behavioral signals from all stores (PostgreSQL, Qdrant, Redis, Kafka logs) within 30 days
- Behavioral signal collection (scroll, dwell, zoom — Phase 2+) requires explicit disclosure and consent extension

**EU AI Act:**
- Echo's recommendation system influences purchasing decisions — subject to transparency requirements
- Architectural advantage: LLM handles conversation and persona extraction only; product matching is deterministic vector similarity (cosine distance) — explainable and auditable without per-recommendation justification
- No opaque neural ranking in the recommendation path — re-ranking stage uses explicit business rules, not learned weights

**Consumer Protection / E-commerce:**
- Existing platform handles returns, consumer rights, pricing transparency, and transaction compliance — Echo inherits this entirely
- Echo does not modify pricing, availability, or transaction flow — it only changes the discovery path to products

### Technical Constraints

**AI Cost & Latency Budget:**
- LLM tokens are the largest variable cost: $0.02–0.10 per 10–15 exchange session
- Per-recommendation explainability deferred — additional LLM call per recommendation set not justified for MVP cost/latency. Revisit if customer demand materializes
- Model tiering: cheaper models (Haiku-class) for classification and feature extraction; expensive models (Opus-class) for nuanced discovery conversations
- Token budgets per conversation: discovery sessions should converge within 10–15 exchanges

**Data Isolation:**
- Persona vectors, conversation logs, and behavioral signals isolated per user — no cross-user data leakage in vector DB queries or LLM context
- LangGraph thread isolation via `user_id` in run config
- Aggregate analytics use anonymized, differential-privacy-protected data only

**Sponsored Products Guardrail (Post-MVP):**
- Promoted placements must pass a taste-relevance threshold (minimum cosine similarity to persona vector) — enforced in the re-ranking stage, not as a policy overlay
- Design decision deferred: what happens when a brand pays but product falls below relevance threshold. Sponsored products cut from v1

### Integration Requirements

- Echo integrates with existing platform product catalog, user accounts, authentication, payments, shipping, and returns — no new commerce infrastructure
- CDC (Change Data Capture) pipeline needed when transitioning from dummy data to real catalog (Phase 3)
- Echo exposes new API surfaces: SSE for LLM streaming, WebSocket for real-time interactions; consumes existing platform APIs

### Domain Risk Mitigations

| Risk | Mitigation |
|---|---|
| Taste profile data breach | Encrypt at rest and in transit; per-user isolation in vector DB; store derived vectors, not raw conversation transcripts |
| LLM generates misleading product claims | LLM generates conversation only — never product descriptions, pricing, or availability. Product data served from catalog directly |
| Recommendation filter bubble | Diversity constraints in re-ranking (MMR); monitor recommendation diversity metrics; exploration-exploitation balance |
| GDPR deletion leaves orphaned data | Deletion pipeline covers PostgreSQL, Qdrant, Redis cache, and Kafka event logs |

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. Elimination-First Product Discovery**
Traditional e-commerce relies on search (requires vocabulary) or collaborative filtering (requires history). Echo inverts the model: rejection is the primary input signal. Users reveal taste by what they don't want, which is cognitively easier and requires zero domain vocabulary. No competitor in the home products vertical uses this approach. Cross-pollination source: Stitch Fix proved "the return reason is more valuable than the purchase."

**2. Conversation as Vector Operation**
The chat agent and recommendation engine operate in the same embedding space. Each message, swipe, and rejection mathematically adjusts the persona vector that drives ANN retrieval. Conversation IS search, not a layer on top of search.

**3. Taste Profile as Persistent, Multi-Faceted Identity**
Unlike recommendation history (a list of past actions), Echo's taste profile is a living vector representation that captures preferences across rooms, categories, and contexts. It evolves continuously, is never "complete" (diminishing returns curve), and becomes the primary retention mechanism — a switching cost that grows with every interaction.

**4. Enhancement-Layer Architecture**
Echo layers onto an existing production platform — graceful degradation to current experience if AI underperforms, built-in A/B baseline from Day 1, no chicken-and-egg problem for users or catalog.

### Market Context & Competitive Landscape

No incumbent combines conversational AI discovery across furniture, kitchen/bath, building materials, and design services in a single taste profile:
- **Havenly AI:** Designer-curated, iOS-only, no elimination-based discovery
- **Houzz Pro:** Professional tools, not consumer AI discovery
- **Amazon Rufus:** Mass market, breadth optimization — no domain depth
- **Google Vertex Conversational Commerce:** Generic retail infrastructure, no domain specialization
- **Modsy:** Shut down 2022 — subscription model not sustainable; Echo's transaction model is structurally different

Market data: Furniture e-commerce $33.5B → $51.6B by 2035. AI interior design market $7.3B by 2033 (24.3% CAGR). 52% of consumers overwhelmed by choice. Only 1 in 10 finds what they want via keyword search.

### Innovation Validation

| Innovation | How to Validate | When |
|---|---|---|
| Elimination-first discovery | Rejection signals measurably move persona vector toward relevant products within 90 seconds | MVP |
| Conversation as vector operation | Conversational input produces same vector adjustments as explicit swipe input | MVP |
| Taste profile retention | 30-day return rate for users with established profiles vs. new users | Phase 2+ |
| Enhancement-layer degradation | Platform functions normally with Echo AI disabled; A/B test assisted vs. unassisted | MVP |

### Innovation Risk & Fallbacks

| Innovation Risk | Fallback |
|---|---|
| Elimination signals too noisy for useful persona vector | Fall back to structured preference questions before free-form elimination |
| Embedding quality can't distinguish meaningful style differences | Broader category-level matching; refine to style-level as embeddings improve (Phase 2) |
| Users don't engage with conversational discovery | Keep traditional search fully functional; Echo as optional discovery mode |
| Taste profile doesn't drive retention | Profile still valuable for in-session quality — retention becomes bonus, not thesis |

## Web Application Requirements

### Architecture

Echo is a hybrid Next.js web application: SSR for catalog pages and the broader platform, SPA-like experience for the discovery conversation. The discovery UI is a real-time, stateful interaction (chat + product reactions + live recommendation updates) running within the existing platform shell.

**Rendering Strategy:**
- **SSR:** Product catalog pages, platform navigation, account pages — via Next.js App Router
- **Client-Side SPA:** Echo discovery conversation — persistent WebSocket/SSE connections, real-time state, no full-page reloads during discovery
- **React Server Components:** Static product data display; client components for interactive discovery elements

**Browser & Device Support:**
- **Desktop-first** — primary use case is home renovation research at desk/laptop
- **Responsive to tablet** — secondary browsing context
- **Mobile functional but not optimized** — conversation UI usable but not gesture-optimized for MVP
- Modern evergreen browsers: Chrome, Firefox, Safari, Edge (latest 2 versions)

**Real-Time Communication:**
- **SSE:** LLM token streaming — one-way server→client, `text/event-stream`
- **WebSocket:** Bidirectional for swipe events, rejection signals, live recommendation updates
- **No WebRTC** for MVP — voice interaction cut from v1

### Responsive Design

- **Desktop (1024px+):** Split-view — conversation panel left, product recommendation grid right
- **Tablet (768–1024px):** Stacked or toggle between conversation and recommendations
- **Mobile (< 768px):** Single-column, conversation-first. Not optimized for swipe gestures in MVP

### State Management

- Discovery session state managed server-side via LangGraph checkpoints (PostgreSQL) — client reconnects resume exactly where they left off
- Client-side state limited to UI concerns (active panel, scroll position, animation state)
- No client-side persona vector storage — all persona computation server-side

### API Surface

- **GraphQL:** Product recommendation queries (field-level selection, single round-trip for product + images + pricing + confidence)
- **SSE endpoint:** LLM conversation streaming
- **WebSocket endpoint:** Real-time interactions (swipes, rejections, behavioral signals in later phases)
- **REST:** Account, session management, platform integration

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Demo MVP — concept validation with dummy data proving the elimination-first discovery loop end-to-end. Must be compelling enough for investors and partners. Not a production launch.

**Resource Reality:** Solo founder (Yushi) with AI-assisted development tools. No team. Existing platform provides commerce infrastructure — Echo MVP builds only the AI discovery layer.

**Timeline Target:** As fast as possible. Critical path: embedding pipeline → LangGraph agent → discovery UI → recommendation serving.

**Speed Principle:** Every scope decision optimizes for time-to-working-demo. If a feature doesn't contribute to proving the core loop (react → persona updates → recommendations improve), it's cut.

### MVP Feature Set (Phase 1)

**Core Journey Supported:** Sarah's Kitchen (Journey 1) — first-time homeowner discovers products through elimination-first conversation.

**Must-Have Capabilities:**

| Capability | Why It's Must-Have | Implementation |
|---|---|---|
| Product catalog embedding | Foundation — nothing works without it | Embed dummy products using CLIP/Marqo into Qdrant |
| LangGraph conversational agent | Core interaction — greeting → discovery → recommend cycle | Basic stateful graph with checkpoint persistence |
| Elimination-first UI | The differentiator — reject/approve products with natural language | Desktop split-view: chat left, product cards right |
| Thin persona creation | The proof — rejection signals move the persona vector | Single-facet vector updated from conversation + rejections |
| Recommendation serving | The payoff — persona vector → product retrieval via cosine similarity | Qdrant ANN search, basic ranking |
| Session persistence | The retention signal — returning users resume from existing profile | LangGraph checkpoints in PostgreSQL |

**Explicitly Not in Demo MVP:**
Multi-facet personas, behavioral signals, feedback buttons, taste bar UI, confidence language, photo upload, architect modules, sponsored products, taste export, demand gap detection, CDC pipeline, Kafka event streaming, MLOps, A/B testing framework, admin dashboard (FR30–FR33 deferred to Phase 2 — MVP observability via raw logs and direct DB queries).

**Contingency Scope Narrowing:**
If embedding quality proves harder than expected, narrow from all product categories to a single category (e.g., kitchen fixtures only). Proving the loop in one category is sufficient for a demo.

### Post-MVP Roadmap

**Phase 2 — Feedback Layer (after demo validated):**
- Rejection feedback buttons (2-second preset) for faster signal collection
- Behavioral signal collection (scroll, dwell, zoom) via Kafka event pipeline
- Persona refinement from multi-signal input (explicit + behavioral)
- Real catalog embeddings replacing dummy data
- Basic admin dashboard: session replay, persona vector visualization, recommendation quality metrics

**Phase 3 — Engagement (after feedback loop proven):**
- Taste profile bar UI (never-full, diminishing returns)
- Confidence language tied to profile completeness
- Multi-faceted persona portfolios (per room/context)
- Photo upload (multimodal embedding pipeline)
- CDC pipeline for real-time catalog sync

**Phase 4 — Intelligence (after retention validated):**
- Conversational vector steering (chat as mathematical interface to recommendations)
- Emergent archetype clustering from embedding space
- Demand gap detection informing procurement
- Full MLOps pipeline (automated retraining, A/B testing)
- Sponsored products with taste-relevance threshold enforcement
- Taste profile export (data portability)
- Architect-specific modules and multi-client profiles

### Risk Mitigation Strategy

**Technical Risks:**

| Risk | Likelihood | Mitigation | Contingency |
|---|---|---|---|
| Embedding quality insufficient | Medium | Start with pre-trained CLIP/Marqo; manually evaluate clusters before building UI | Narrow to single category; broader category-level matching |
| LangGraph complexity slows development | Low-Medium | Start with simplest graph (3 nodes); add complexity only when needed | Simpler chain-based approach without full graph state |
| Dummy data lacks real catalog diversity | Medium | Create data covering the style spectrum with deliberate variety | Use subset of real catalog products instead |

**Market Risks:**

| Risk | Mitigation |
|---|---|
| Users don't engage with conversational discovery | Demo tests this directly — if testers don't engage past 90 seconds, rethink before investing further |
| Competitive window narrows | Speed-to-demo is the mitigation — validate fast, then decide on investment |

**Resource Risks:**

| Risk | Mitigation |
|---|---|
| Solo founder bottleneck | Prioritize critical path ruthlessly: embeddings → agent → UI. AI tools for boilerplate. No polish until loop works |
| Embedding quality requires ML expertise | First hire decision point: if demo validates but quality needs work, hire ML engineer before Phase 2 |
| Timeline extends beyond useful window | Pre-planned narrowing: all categories → single category → single subcategory |

## Functional Requirements

### Conversational Discovery

- **FR1:** Customer can initiate a discovery conversation by describing what they're working on
- **FR2:** Customer can reject recommended products with natural language feedback
- **FR3:** Customer can approve or express interest in recommended products
- **FR4:** Customer can provide freeform taste descriptions during conversation
- **FR5:** System can present a curated set of product recommendations after each conversational exchange
- **FR6:** System can adjust recommendations in real-time based on rejection and approval signals within the same session
- **FR7:** System can conduct a multi-turn discovery conversation that converges toward relevant recommendations within 10-15 exchanges

### Taste Profile Management

- **FR8:** System can create a taste profile from a customer's first discovery session
- **FR9:** System can update the taste profile based on each rejection, approval, and conversational input
- **FR10:** Customer can resume a discovery session with their existing taste profile without re-discovery
- **FR11:** System can apply the taste profile across all product categories on the platform
- **FR12:** Customer can reset their taste profile and start fresh

### Product Recommendation

- **FR13:** System can retrieve relevant products from the catalog based on the customer's current taste profile
- **FR14:** System can rank retrieved products by relevance to the taste profile
- **FR15:** System can apply diversity constraints to avoid showing only one brand, style, or subcategory
- **FR16:** System can display product recommendations with images, name, and pricing
- **FR17:** System can surface products the customer did not explicitly search for but that match their taste profile

### Product Catalog Embedding

- **FR18:** System can generate vector embeddings for products in the catalog (text and image attributes)
- **FR19:** System can store and index product embeddings for fast similarity search
- **FR20:** System can match persona vectors against product embeddings using similarity search
- **FR21:** Admin can add new dummy products to the embedded catalog

### Platform Integration

- **FR22:** Customer can access Echo discovery from the existing platform navigation
- **FR23:** Customer can view full product details for any recommended product via existing product pages
- **FR24:** Customer can add recommended products to their cart or project directly from the Echo interface
- **FR25:** System can fall back to existing platform browsing if the Echo AI layer is unavailable

### Session & Conversation Management

- **FR26:** System can persist conversation state across browser sessions
- **FR27:** System can stream AI responses token-by-token to the customer in real-time
- **FR28:** Customer can start a new discovery conversation while retaining their existing taste profile
- **FR29:** System can track the number of exchanges and recommendation interactions per session

### Admin & Observability (Phase 2)

- **FR30:** Admin can view session-level metrics (session count, exchanges per session, recommendation CTR)
- **FR31:** Admin can replay a customer's discovery session showing persona vector evolution
- **FR32:** Admin can inspect the embedding space to identify product clusters and coverage gaps
- **FR33:** Admin can monitor system health (API availability, recommendation latency, LLM response times)

## Non-Functional Requirements

### Performance

| Requirement | Target | Context |
|---|---|---|
| Recommendation retrieval (non-LLM path) | < 100ms P99 | ANN search + ranking + re-ranking |
| LLM first token latency | < 500ms | Conversational response starts streaming |
| Full recommendation refresh cycle | < 2s | Rejection → persona update → new recommendations rendered |
| Echo conversation launch | < 1.5s | "Start Discovery" click to first AI greeting |
| Swipe/rejection visual acknowledgment | < 50ms | Optimistic UI before server confirms |
| Product page load (SSR) | < 2.5s LCP | Standard e-commerce web vitals |
| Concurrent discovery sessions (MVP) | 15-20 simultaneous | Beta testing with invited users |

### Security

- All data encrypted at rest (AES-256) and in transit (TLS 1.3)
- Per-user isolation for persona vectors, conversation logs, and behavioral signals — no cross-user data leakage in vector DB queries or LLM context
- LangGraph thread isolation enforced via `user_id` in run configuration
- Authentication inherited from existing platform (OAuth 2.0 + JWT)
- LLM prompts must not expose internal system architecture, embedding dimensions, or recommendation logic
- Rate limiting on conversation endpoints (token budget per session)

### Scalability

- **MVP scale:** 15-20 concurrent beta users, ~100-500 dummy products, single-instance deployment acceptable
- **Post-MVP scale path:** Architecture supports horizontal scaling per service without re-architecture
- **Vector DB:** Qdrant handles 10x catalog growth (to ~5,000 products) with < 20% latency degradation
- **LLM cost scaling:** Cost per session < $0.10; model tiering enforced from Day 1

### Accessibility

- WCAG 2.1 AA compliance for all Echo UI components
- Keyboard navigation for all interactive elements (product cards, chat input, rejection/approval actions)
- Screen reader support for streamed AI responses (progressive announcement)
- Alt text for all product images in recommendation cards
- No gesture-only interactions — all swipe actions have button/keyboard alternatives

### Reliability

- **System availability:** > 99.9% for existing platform; Echo AI layer may have lower availability with graceful degradation to standard browsing
- **Conversation state durability:** LangGraph checkpoints persisted to PostgreSQL — no loss on server restart
- **Taste profile durability:** Persona vectors stored in Qdrant (serving) and PostgreSQL (backup)

### Data Privacy

- Taste profile data classified as personal data under GDPR
- Consent collected at account creation, disclosed in privacy policy
- Right to erasure: account deletion purges all persona data from all stores within 30 days
- Data architecture supports future right-to-portability export (Phase 4)
- No cross-user data in LLM context windows
- Aggregate analytics use anonymized data only

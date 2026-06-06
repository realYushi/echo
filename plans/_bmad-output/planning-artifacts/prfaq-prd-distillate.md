---
title: "PRFAQ Distillate: Echo"
type: llm-distillate
source: "prfaq-prd.md"
created: "2026-04-12"
purpose: "Token-efficient context for downstream PRD creation"
---

## Product Identity

- **Name:** Echo — "your taste, reflected back"
- **One-liner:** AI-powered discovery engine that helps homeowners find products they can't describe, by learning from what they reject
- **Concept type:** Commercial product — AI enhancement layer on an existing running e-commerce platform
- **Positioning:** Mid-to-high-end home products (furniture, kitchen/bath fixtures, lighting, building materials, electrical, design services)
- **Target customer:** Homeowners furnishing or renovating — especially first-timers who have taste but lack design vocabulary
- **Architect persona:** Identified as secondary audience in brainstorming but excluded from v1 press release and FAQ; consumer story stands alone

## Core Thesis

- Customers cannot articulate preferences in design language — elimination (rejection) is cognitively easier than selection
- The recommendation engine and chat agent are not separate features — they operate in the same vector space; conversation IS the search
- The taste profile is simultaneously the product's UX, its retention mechanism, and its competitive moat
- "Enhancement, not replacement" — Echo layers onto an existing platform with existing customers, catalog, and commerce infrastructure; graceful degradation to current experience if AI underperforms

## Rejected Framings and Why

- "AI Shopping Assistant" headline — too generic, replaced with "Helps Homeowners Discover Products They Can't Describe" (more provocative, customer-centric)
- "Conversation and elimination" in subheadline — internal language; replaced with "reacting to what they see, not searching for what they can't name"
- Leader quote options: (A) ambition/where Echo is going, (B) market critique/why competitors are wrong — both rejected in favor of (C) emotional bet: "Everyone has taste. Not everyone has the words for it." Positions Echo as thesis about future of commerce, not feature description
- "Everyone" as target market — rejected; honest positioning is mid-to-high-end. "If you're furnishing with flat-pack basics, we're probably not the right fit today."
- "No account required" — rejected because not true for the platform

## Requirements Signals

- **Elimination-first discovery:** Show products, learn from rejections. "Too bulky" or "not warm enough" adjusts persona vector in real time. Speed-to-value target: 90 seconds to first relevant recommendation
- **Multi-faceted taste profile:** Separate taste facets per room/context (kitchen style ≠ bedroom style). Users can create, reset, or branch facets without losing other data
- **Cross-category profile:** Single taste profile spans furniture, fixtures, lighting, materials — "sofa to shower head to floor tile"
- **Taste profile export:** Downloadable. Data portability as trust signal (counters Modsy shutdown concern)
- **Sponsored products guardrail:** Brands can pay for promoted placement, but promoted products MUST pass taste-relevance threshold or they don't show. This is a technical requirement, not just policy — must be enforced in the re-ranking stage
- **Photo upload:** NOT launch feature. Coming later. Conversation-based description workaround for v1. Expected to be #1 feature request Day 1
- **Demand gap detection:** Phase 5 feature. Aggregate taste data identifies product categories with high persona interest but low catalog coverage. Informs procurement decisions
- **Profile never "complete":** Taste bar UX with diminishing returns curve — gamification + retention + honest representation that taste evolves

## Technical Context and Constraints

- **Embedding pipeline:** Vision model → rich product description → lightweight LLM extracts structured attributes → embed into vector space. Multi-step gives debuggability at each stage vs. end-to-end CLIP
- **Stack (from technical research):** LangGraph (agent orchestration) + LlamaIndex (RAG/retrieval) + Qdrant (vector DB) + Kafka (events) + FastAPI (backend) + Next.js (frontend) + PostgreSQL + Redis
- **Three-stage recommendation funnel:** Retrieval (<10ms, ANN search) → Ranking (<30ms, feature-based) → Re-ranking (<10ms, diversity + business rules). Total non-LLM path <100ms
- **LLM/embedding separation:** LLM handles conversation and persona extraction ONLY. Product matching is deterministic vector similarity (cosine distance). LLM never directly selects or ranks products. This is both an engineering decision and a regulatory positioning advantage
- **Architecture must be cloud-agnostic** at the application layer (GCP recommended but not locked in)
- **MVP uses dummy data** to validate the discovery loop end-to-end before committing to production catalog embeddings

## Competitive Intelligence

- **No incumbent combines** conversational AI discovery across furniture + building materials + design services — domain is fragmented
- **Havenly AI:** Designer-curated rooms, photo upload, iOS app only. No elimination-based discovery, no building materials scope
- **Houzz Pro:** Product sourcing and project management for professionals. Not consumer-facing AI discovery
- **ConversionBox AI:** Search augmentation for furniture e-commerce. No persistent taste profile, no conversational elimination flow
- **Google Vertex Conversational Commerce Agent:** Generic retail infrastructure. No domain specialization
- **Material Bank:** B2B architecture materials marketplace. Sample logistics, not consumer recommendation
- **Amazon Rufus:** 250M users, 60% conversion lift. Mass market, breadth optimization. Threat at the platform layer, not the domain layer
- **Modsy:** Shut down 2022. Design service model (subscription fees) was not sustainable. Echo's commerce model (transaction revenue) is structurally different
- **Market data:** Furniture e-commerce $33.5B→$51.6B by 2035. AI interior design market $7.3B by 2033 (24.3% CAGR). 52% consumers overwhelmed by choice. 80% more likely to purchase with personalization. Only 1 in 10 finds what they want via keyword search

## Open Questions and Unknowns

- **Current platform AOV and conversion rate:** Unknown. Needed to ground unit economics before any investor conversation
- **Catalog depth per category:** Is there enough variety in each product category to support meaningful recommendations? Needs honest category-by-category assessment
- **90-second speed-to-value:** Untested with real users. Bold claim in press release. Must validate with prototype
- **Embedding quality on real home products:** Can the pipeline distinguish "warm minimalist Scandinavian" from "cold industrial Scandinavian"? Only testable by embedding real products and evaluating clusters
- **Sponsored products technical design:** How is taste-relevance threshold enforced in re-ranking? What happens when a brand pays but product doesn't match persona?

## Scope: In, Out, Maybe

**V1 (MVP with dummy data):**
- IN: Product catalog embedding (all categories), basic LangGraph conversation flow, elimination-first discovery, taste profile creation, vector DB recommendation serving
- OUT: Design services, parking solutions, architect modules, voice interaction, photo upload, demand gap detection, archetype clustering, behavioral signal processing, multi-channel feedback loops

**Fast-follow (Phase 3-4):**
- Photo upload (multimodal embedding)
- Rejection feedback buttons (2-second preset)
- Behavioral signal collection (scroll, dwell, zoom)
- Taste profile bar UI (never-full, diminishing returns)
- Multi-faceted persona portfolios (per room)

**Future (Phase 5):**
- Conversational vector steering (chat as mathematical interface to recommendations)
- Emergent archetype clustering from embeddings
- Demand gap detection for procurement
- Full MLOps pipeline (automated retraining, A/B testing)

## Resource and Timeline Estimates

- **Team today:** Solo founder (Yushi) with existing running platform
- **MVP purpose:** Concept validation ("show the idea"), not production launch
- **Technical research estimate:** 4-6 people, 14 weeks for production MVP — not applicable to concept-proving dummy-data MVP
- **Infrastructure cost:** $3K-8K/mo at MVP scale, $22K-63K/mo at full scale (technical research)
- **LLM cost per session:** $0.02-0.10 per 10-15 exchange conversation
- **First hire priority:** ML engineer with embedding model experience
- **Key risk:** Solo execution speed vs. competitive window. If 18 months instead of 6, Amazon/Google may narrow the gap

## Verdict Summary

- **Overall:** Strong concept built on genuine, market-validated insight. Core thesis survived the gauntlet intact. Risk profile is unusually favorable due to existing platform (enhancement, not greenfield)
- **Forged in steel:** Core insight (vocabulary gap), enhancement-not-replacement strategy, elimination-first UX, taste profile as moat, LLM/embedding separation, competitive gap
- **Needs more heat:** Unit economics (unquantified), 90-second claim (untested), photo upload (missing at launch), sponsored products guardrail (undesigned)
- **Cracks:** Solo founder execution risk, embedding quality unknown until tested on real products, catalog depth may be insufficient for meaningful recommendations in some categories

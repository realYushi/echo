# Natural Chatbot with Claude API

## Goal

Transform the discovery chatbot from a rigid, scripted-feeling Q&A flow into a natural conversational experience that leverages the Anthropic Claude API for genuine dialogue — while keeping the core purpose of building a persona taste profile (likes/hates). Also fix the input focus regression and add suggestion bubbles for low-friction replies.

## Decisions

* **MVP scope**: Focused on persona taste profile building (likes/hates), NOT a general QA chatbot
* **Greet vs discover nodes**: Keep separate for now, unify later after testing
* **Short replies**: Add clickable suggestion bubbles so users can tap common responses instead of typing, while keeping manual input fully available
* **Suggestion generation**: Single Sonnet call returns both the conversational reply and 2-3 suggestion bubbles in a structured format (JSON). No separate Haiku call. Frontend falls back to static suggestions when API key is missing.
* **Tone**: Warm & curious — genuinely interested, not overly chatty. Asks with curiosity, not interrogation.
* **Persona model**: Add `likes: list[str]` and `hates: list[str]` as Claude-synthesized taste descriptors. These become the primary embedding input. Existing granular fields (style_preferences, material_preferences, etc.) stay for heuristic fallback.
* **Category mapping**: Claude maps user intent to the fixed category list (`furniture`, `bathroom`, `kitchen`, `lighting`, `building-materials`) during persona extraction. The extraction prompt includes the allowed values. Heuristic fallback already handles this via keyword matching.
* **Category filtering**: Deferred — categories are captured in persona but Qdrant filtering is not added in this MVP. Categories influence results implicitly through the embedding.

## Requirements

* **R1**: Replace the rigid discovery Q&A with natural, conversational Claude-powered responses that focus on building the persona taste profile
* **R2**: Use proper multi-turn message format when calling Claude API instead of flattening to a single string
* **R3**: Handle varied user inputs gracefully — short answers, long descriptions, vague responses — while steering back toward taste discovery
* **R4**: Maintain input focus after sending a message — no need to click the input field again
* **R5**: Restore input focus after streaming completes (when input becomes re-enabled)
* **R6**: Add clickable suggestion bubbles below the chat input so users can quickly respond without typing
* **R7**: Gently steer off-topic conversation back toward product discovery
* **R8**: Add `likes` and `hates` lists to persona schema as Claude-synthesized taste descriptors
* **R9**: Use likes/hates as the primary embedding input in `persona_to_text()`
* **R10**: Claude maps user-mentioned categories to the fixed product category list during persona extraction

## Acceptance Criteria

* [ ] Chatbot responses feel conversational, not like a scripted questionnaire
* [ ] User can type naturally and the bot adapts its responses accordingly
* [ ] Bot stays on-mission (taste profiling) even when user goes off-topic
* [ ] Suggestion bubbles appear with contextually relevant quick-reply options
* [ ] Clicking a suggestion bubble sends it as a message
* [ ] Manual typing still works alongside suggestion bubbles
* [ ] Input field retains focus after clicking Send or pressing Enter
* [ ] Input field regains focus after bot response finishes streaming
* [ ] Persona `likes` and `hates` lists are populated from conversation
* [ ] Likes/hates are the primary input to persona embedding
* [ ] Categories extracted by Claude match the fixed product category list
* [ ] Persona extraction still works correctly from natural conversation
* [ ] Fallback behavior still works when API key is missing

## Definition of Done

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes

## Out of Scope

* General QA / knowledge-base chatbot functionality
* Qdrant category pre-filtering (deferred — categories influence via embedding for now)
* Changing the SSE streaming mechanism
* Adding conversation persistence across browser sessions (already handled by session resume)
* Unifying greet and discover node prompts (deferred to post-testing)

## Technical Approach

### Backend: Persona schema update
1. Add `likes: list[str]` and `hates: list[str]` to `Persona` model in `backend/app/schemas/persona.py`
2. Update `_PERSONA_SYSTEM_PROMPT` in `backend/app/services/persona.py` to instruct Claude to populate likes/hates as synthesized taste descriptors and map categories to the fixed list
3. Update `persona_to_text()` to use likes/hates as primary embedding input
4. Update `_heuristic_persona()` to populate likes/hates from keyword extraction
5. Update `apply_feedback()` to merge product feedback into likes/hates
6. Update `persona_signal_count()` to include likes/hates

### Backend: Richer Claude conversation
1. Rewrite `_claude_discovery_reply()` in `backend/app/agent/nodes.py` to use proper multi-turn message format (`messages: [{role, content}, ...]`)
2. Expand system prompt: warm & curious tone, persona-building focus, gentle off-topic steering, structured JSON output with `reply` + `suggestions` fields
3. Parse structured response to extract both the assistant message and suggestion bubbles
4. Add `suggestions` field to `AgentState` in `backend/app/agent/state.py`
5. Emit suggestions via SSE event in `backend/app/routers/chat.py`
6. Update fallback path to return static suggestions when API key is missing

### Frontend: Focus fix + suggestion bubbles
1. `ChatInput.tsx`: Add `useRef` on the input element, call `ref.focus()` after submit
2. `ChatInput.tsx`: Add `useEffect` watching `disabled` prop to restore focus when streaming ends
3. New `SuggestionBubbles` component: renders 2-3 clickable pills
4. Wire suggestion bubbles to send message on click (same path as manual typing)
5. Update SSE event handling in `useChat.ts` + `sse.ts` to parse suggestions
6. Update frontend types to include suggestions

## Implementation Plan (small PRs)

* **PR1: Input focus fix** — Add ref-based focus management to `ChatInput.tsx`. Small, self-contained, ships immediately.
* **PR2: Persona likes/hates** — Add likes/hates to schema, update extraction prompt with fixed category list, update embedding function, update heuristic fallback + feedback merge.
* **PR3: Backend conversational upgrade** — Rewrite `_claude_discovery_reply()` with proper multi-turn format, richer system prompt, and structured JSON output (reply + suggestions). Update SSE events and agent state.
* **PR4: Frontend suggestion bubbles** — New `SuggestionBubbles` component, wire to SSE suggestions event, static fallback set, integrate into chat panel.

## Technical Notes

### Key files to modify

**Backend:**
* `backend/app/schemas/persona.py` — Add likes/hates fields
* `backend/app/services/persona.py` — Update extraction prompt, embedding, heuristic, feedback
* `backend/app/agent/nodes.py` — Rewrite `_claude_discovery_reply()`, update system prompt
* `backend/app/agent/state.py` — Add suggestions field
* `backend/app/routers/chat.py` — Emit suggestions SSE event

**Frontend:**
* `frontend/src/components/chat/ChatInput.tsx` — Focus management
* `frontend/src/components/chat/SuggestionBubbles.tsx` — New component
* `frontend/src/components/chat/ChatPanel.tsx` — Integrate suggestions
* `frontend/src/hooks/useChat.ts` — Handle suggestions from SSE
* `frontend/src/lib/sse.ts` — Parse suggestions event
* `frontend/src/types/chat.ts` — Add suggestions type

### Fixed product categories
`furniture`, `bathroom`, `kitchen`, `lighting`, `building-materials`

### Current system prompt (to be replaced)
```
"You are a concise interior product discovery assistant."
"Reply in 1-2 sentences."
"Acknowledge the user's latest signal."
"Ask exactly one next question that helps narrow recommendations."
"Focus on elimination-first discovery."
```

### Current conversation format issue
Messages are flattened into a single string: `"USER: ...\nASSISTANT: ..."` — should use Claude's native multi-turn message array.

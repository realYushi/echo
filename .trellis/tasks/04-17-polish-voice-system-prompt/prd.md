# Polish Gemini Live System Prompt

## Goal

Improve the Gemini Live voice assistant ("Echo") so the conversation feels natural,
stays focused on taste discovery, and opens with a clear, branded greeting. Right now
the model occasionally drifts out of context during random small-talk and the opener
isn't tight.

## What I already know

- The voice system prompt lives **only on the frontend** at
  `frontend/src/hooks/useVoiceChat.ts:16-42` (constant `SYSTEM_INSTRUCTION`),
  passed to Gemini in the `setup` message at line 421.
- Voice greeting is currently triggered by sending a `realtimeInput: { text: "Hello" }`
  after `setupComplete` (line 238-244). The model is instructed to open with three
  things in 2-3 sentences (intro + what happens + concrete opening question).
- Backend persona pipeline (Haiku → Sonnet → CLIP) is decoupled from the conversation
  model and runs against transcripts; nothing here changes the persona side.
- The text-mode Claude prompt (`backend/app/agent/nodes.py:40-59`) is the parallel
  reference for tone — short, warm, on-topic, one question per turn.
- Persona schema (`backend/app/schemas/persona.py`): `budget_tier`, `likes`, `hates`,
  `approvals`, `rejections`. The five taste-signal categories the prompt asks Echo to
  surface map directly to these fields.
- No automated tests assert on the exact wording of `SYSTEM_INSTRUCTION` — the
  `voice-api.test.ts` covers the API surface only. Changes are low-risk to ship.

## Problem analysis (current prompt weaknesses)

1. **Greeting is loose.** The prompt describes *what* the greeting should do (3 bullets)
   but lets Gemini paraphrase the brand-name intro freely. User wants a more focused,
   on-brand opener that always starts "Hi, this is Echo, and I'm here to help."
2. **Off-topic drift.** Rule says "briefly acknowledge and gently steer back" but gives
   no concrete pattern. In practice Gemini will follow tangents (weather, jokes,
   personal questions) for several turns before returning.
3. **Tone instructions are abstract.** "Sound genuinely curious and encouraging,
   like a knowledgeable friend" — no concrete phrasing examples for Gemini to anchor on.
4. **Wrap-up is vague.** "When you have a good sense" gives no signal-count threshold
   or example wording for handing off to the recommendation panel.
5. **Voice-medium reminders are thin.** Only "no bullet points" is called out. Live
   audio also wants: no markdown, no spelling-out URLs, no over-long lists, contractions,
   pacing pauses for user response.

## Requirements

- Replace the `SYSTEM_INSTRUCTION` constant in `useVoiceChat.ts` with a polished version that:
  - Locks the opening line: **"Hi, this is Echo, and I'm here to help you discover your style."**
    (or close variant — exact wording TBD with user) followed by a short framing sentence
    and one concrete opening question.
  - Adds an explicit **off-topic redirect pattern** with 1-2 example phrasings Gemini can
    mimic (e.g., "That's a fun aside — let's get back to your style. …").
  - Keeps the five taste categories (style, material, color, texture/finish, budget)
    aligned with the persona schema.
  - Adds **voice-medium constraints**: contractions, no markdown/URLs/lists, one short
    question per turn, brief affirmations ("got it", "love that") to feel conversational.
  - Tightens the wrap-up rule with a soft signal threshold (e.g., "once you have ~3-4
    distinct taste signals across categories") and an example closing line.
- Ensure the constant is still passed to Gemini exactly as before (no surrounding code
  changes unless the greeting trigger needs adjustment).

## Acceptance Criteria

- [x] Prompt lives in `_VOICE_SYSTEM_INSTRUCTION` in `backend/app/services/voice.py`
      and is baked into the ephemeral token's `live_connect_constraints.config`.
- [x] Opening line begins with the agreed greeting verbatim.
- [x] At least one explicit example of an off-topic redirect phrasing is included.
- [x] At least one explicit example of a wrap-up phrasing is included.
- [x] Voice-medium constraints (no markdown, contractions, one question/turn) are stated.
- [x] Manual smoke test: user verified the opener fires verbatim, the assistant stays on
      topic through a full 5-category discovery run (style → material → finish → color →
      budget), and the wrap-up no longer points at any UI panel.
- [x] No regression in `frontend/src/lib/voice-api.test.ts` (27/27 frontend tests pass)
      or backend `test_voice_router.py` (23/23 backend tests pass).

## Definition of Done

- Tests added/updated where applicable (likely none — prompt is a string constant).
- `pnpm lint` / `pnpm typecheck` green.
- Manual voice-mode smoke test recorded in journal.

## Out of Scope

- Changing the backend persona pipeline, Claude prompts, or persona schema.
- Switching Gemini model, voice (Aoede), or audio config.
- Changing the greeting trigger mechanism (still send `"Hello"` realtime input after
  setupComplete) unless we decide a `clientContent` priming turn is required.
- Internationalization / non-English personas.
- Adding tool calls / function calling for taste extraction.

## Decisions (from user)

- **Greeting flow**: "Help + what-I-do + question" — also explicitly tell the user they
  can share what they like *or* what they want to avoid (mirrors the persona's likes/hates
  duality).
- **Off-topic handling**: Soft redirect — one warm acknowledgment then pivot back to a
  taste question.
- **Test surface**: ignore — manual smoke test only, no fixture work needed.
- **Wrap-up phrasing**: do NOT direct user to "the picks on the right" or any UI panel.
  Thank → "I have enough for now" → "feel free to keep adding, or close any time" →
  "I'll keep polishing the profile from your likes/dislikes later." If user adds more
  after wrap-up, treat as a normal turn (don't re-wrap).
- **Prompt location**: moved from frontend to **backend**. See key-discovery below.

## Key discovery during testing

First end-to-end smoke test surfaced that Gemini ignored the system instruction entirely
("I'm a large language model, created by Google. … I can help you find a chair"). Root
cause: the WebSocket endpoint we use (`BidiGenerateContentConstrained`, see
`useVoiceChat.ts:13-14`) silently drops any `setup.systemInstruction` not declared in
the ephemeral token's `live_connect_constraints.config`. Fix: bake `system_instruction`
into the constraints when minting the token in `backend/app/services/voice.py`, and
remove the now-ignored `systemInstruction` from the client setup.

This means **the prompt now lives on the backend only**. Single source of truth, harder
to tamper from the browser.

## Final implementation

- `backend/app/services/voice.py`:
  - New module-level constant `_VOICE_SYSTEM_INSTRUCTION` containing the full prompt
    (4-part structure aligned to Google's Live API best-practices guide:
    Persona → Conversational Rules (one-time + loop + wrap-up) → Guardrails).
  - Injected as `live_connect_constraints.config.system_instruction` in
    `create_ephemeral_token`.
- `backend/pyproject.toml`: per-file ruff ignore for `E501` on
  `app/services/voice.py` (the prompt is natural-language paragraphs, reformatting hurts
  readability; code in this file is short and not affected).
- `frontend/src/hooks/useVoiceChat.ts`:
  - Removed `SYSTEM_INSTRUCTION` constant.
  - Removed `systemInstruction` field from `setup` payload (was being silently dropped).

## Technical Notes

- Files touched: `frontend/src/hooks/useVoiceChat.ts` only (string constant).
- Reference: text-mode prompt at `backend/app/agent/nodes.py:40-59`.
- Persona shape: `backend/app/schemas/persona.py` (5 fields).
- Voice greeting trigger: `useVoiceChat.ts:238-244` (`realtimeInput.text = "Hello"`).
- Risk: extremely low — string change, no API/contract change, no test impact.

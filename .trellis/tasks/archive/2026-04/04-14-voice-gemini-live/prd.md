# Voice Conversation with Gemini Live API

## Goal

Add voice-first taste discovery using Gemini Live API alongside the existing text chat. The customer speaks naturally with the agent, while the existing Claude-powered persona pipeline (Haiku post-process → Sonnet persona build → CLIP embedding) runs asynchronously in the background processing transcripts to drive product recommendations. Gemini relies on its own conversation history to stay personalized — no mid-session context injection needed. Text chat remains as fallback for users without microphones or in public settings.

## What I already know

* Current architecture: text chat via Claude (Sonnet) with JSON-structured responses, SSE streaming to frontend
* Persona pipeline: three-stage (Haiku signal detection → Sonnet persona build → CLIP embedding), already decoupled from conversation model
* Gemini Live API uses WebSocket (WSS) for bidirectional audio streaming
* Native speech-to-speech — single model handles audio in/out, no separate STT/TTS needed
* Supports system instructions, function calling, `sendClientContent` for injecting context mid-session
* Provides text transcripts alongside audio output
* JS SDK: `@google/genai` with ephemeral token support for browser-to-API connections
* Pricing: ~$0.005/min input + $0.018/min output audio
* Session limits: 15 min without compression, unlimited with sliding window compression + resumption

## Assumptions (temporary)

* Gemini Live will follow discovery system prompts well enough for taste profiling
* Gemini's own conversation history is sufficient for personalization (no mid-session context injection needed)
* Browser Web Audio API / AudioWorklet is sufficient for MVP (no need for WebRTC/LiveKit yet)
* Ephemeral tokens work for securing browser-to-Gemini connections

## Open Questions

(resolved — see decisions below)

## Requirements

### Voice conversation (primary mode)
* Real-time voice conversation between customer and Gemini Live agent
* System prompt configures Gemini as Echo discovery assistant (warm, curious, one question at a time)
* Gemini provides text transcripts per turn
* Transcripts sent to backend, processed by existing Haiku → Sonnet → CLIP pipeline (non-blocking, async) to drive product recommendations
* Gemini naturally adapts conversation based on its own conversation history (no mid-session injection needed)

### Text chat (fallback mode)
* Existing text chat remains fully functional as fallback
* User can choose voice or text at session start
* If voice fails (Gemini disconnect, mic permission denied, network error), gracefully fall back to text mode with clear error message
* Both modes feed into the same persona pipeline

### Frontend
* Voice mode: mic button to start/stop, visual indicator of speaking state
* Conversation transcripts displayed in chat panel during voice mode (so user can see what was said)
* Taste profile panel updates in real-time during voice conversation (existing behavior)
* Product recommendations refresh as persona evolves (existing behavior)
* Like/dislike on product cards stays visual (click-based, not voice)

### Backend
* New endpoint to generate Gemini ephemeral tokens
* Transcript relay endpoint: receives turn transcripts, feeds into persona pipeline
* Persona update pushes to frontend (SSE/WS) to update taste profile and product recommendations

## Acceptance Criteria

* [ ] User can choose between voice and text mode on the discover page
* [ ] Voice mode: Gemini Live agent conducts taste discovery conversation
* [ ] Conversation transcripts are captured and displayed turn-by-turn
* [ ] Transcripts trigger existing persona pipeline (Haiku → Sonnet → CLIP) asynchronously
* [ ] Persona updates drive product recommendation refresh (not injected into Gemini)
* [ ] Taste profile panel updates in real-time during voice conversation
* [ ] Product recommendations refresh as persona evolves
* [ ] Gemini disconnect → automatic fallback to text mode with clear error message
* [ ] Mic permission denied → fallback to text mode with clear error message
* [ ] Session handles reconnection gracefully (session resumption)
* [ ] Text mode works exactly as before (no regression)

## Decision (ADR-lite)

**Context**: Voice conversation needs a real-time speech-to-speech model. Options: (A) Gemini Live native speech-to-speech, (B) STT + Claude + TTS pipeline, (C) OpenRouter text model + separate STT/TTS.

**Decision**: Gemini Live for voice conversation, Claude stays for persona pipeline. Hybrid approach.

**Consequences**: Two model providers to manage. But: Gemini Live gives native speech-to-speech (no STT/TTS latency), existing persona pipeline stays untouched, and the architecture is cleanly separated (conversation model vs. analysis model).

**Scope decisions**:
* Voice is primary, text is fallback — not a toggle mid-session (if voice fails, fall back to text with error message)
* No mid-session persona injection — Gemini's conversation history handles personalization, persona pipeline drives recommendations only
* Product like/dislike stays click-based — no verbal feedback for MVP
* Focus on persona building phase only, not the update/refinement phase

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Out of Scope (explicit)

* WebRTC / LiveKit integration (future optimization)
* Video/camera input (future — Gemini Live supports it)
* Multi-language support (English first)
* Replacing Claude in the persona pipeline with Gemini
* Mobile-specific audio handling
* Verbal product feedback ("I like that one")
* Mid-session mode switching (voice↔text) — if voice fails, it's a one-way fallback
* Persona update/refinement phase (focus on initial building only)

## Technical Notes

* **Approach**: Raw WebSockets (no SDK) — simple JSON messages, full control over connection lifecycle
* **WebSocket endpoint**: `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=API_KEY`
* **Ephemeral token endpoint** (for browser): `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained?access_token={token}`
* **Model**: `gemini-3.1-flash-live-preview`
* **Audio format**: Input 16-bit PCM 16kHz little-endian, Output 16-bit PCM 24kHz
* **Message protocol**: JSON — `BidiGenerateContentClientMessage` / `BidiGenerateContentServerMessage`
* **Session config**: First message is `BidiGenerateContentSetup` with model, responseModalities, systemInstruction
* **Transcripts**: `inputTranscription` and `outputTranscription` in server messages
* **No mid-session injection**: Gemini uses its own conversation history for personalization; persona pipeline output drives product recommendations only
* **Ephemeral tokens**: Backend creates short-lived tokens so API key is never exposed to browser
* **Reference example**: https://github.com/google-gemini/gemini-live-api-examples/tree/main/gemini-live-ephemeral-tokens-websocket
* **Existing persona pipeline**: `backend/app/services/persona.py`, `backend/app/agent/nodes.py`
* **Existing frontend chat**: `frontend/src/components/chat/`, `frontend/src/hooks/useChat.ts`

## Architecture

```
Browser                                  Backend
┌─────────────────────────┐
│  Mode Selection         │
│  [🎤 Voice] [💬 Text]  │
└────────┬────────────────┘
         │
    ┌────▼─────────────────────────────────────────┐
    │ VOICE MODE                                    │
    │                                               │
    │  Browser ◄──WebSocket──► Gemini Live API     │
    │  (mic/speaker)           (speech-to-speech)   │
    │                               │               │
    │                          transcript           │
    │                               ▼               │
    │                     ┌──────────────┐          │
    │                     │   Backend    │ async    │
    │                     └──────┬───────┘          │
    │                            │                  │
    │              ┌─────────────┼──────────┐       │
    │              ▼             ▼           ▼      │
    │           Haiku        Sonnet       CLIP      │
    │         (signals)    (persona)    (embed)     │
    │              │             │           │      │
    │              └─────────────┼──────────┘       │
    │                            ▼                  │
    │              Persona Update                   │
    │              → push to frontend               │
    │              → trigger product recommendations│
    └───────────────────────────────────────────────┘
    ┌───────────────────────────────────────────────┐
    │ TEXT MODE (fallback, or user choice)          │
    │  Existing Claude chat + persona pipeline      │
    │  (unchanged)                                  │
    └───────────────────────────────────────────────┘

    On voice failure → auto-fallback to text mode
                       with clear error message
```

## Implementation Plan

### Research Spike (pre-implementation)
* Study Google's ephemeral tokens WebSocket example for browser audio/WebSocket patterns
* Validate ephemeral token creation from Python backend
* Document AudioWorklet patterns for PCM streaming

### PR1: Backend — Gemini ephemeral token endpoint + transcript relay
* New endpoint: `POST /voice/token` — generates Gemini ephemeral token, returns to frontend
* New endpoint: `POST /voice/transcript` — receives turn transcript, fires async persona pipeline
* Add `GEMINI_API_KEY` to config/settings
* Persona update notification channel (SSE or WS) to push updates to frontend
* Tests for token generation and transcript processing

### PR2: Frontend — Voice session manager + audio pipeline
* `useVoiceChat` hook: manages Gemini Live WebSocket connection, audio capture/playback
* AudioWorklet for PCM streaming (based on research findings from web console starter)
* Transcript capture from Gemini's audio transcription output
* Send transcripts to backend `/voice/transcript` endpoint
* Receive persona updates via SSE (existing pattern)
* Connection lifecycle: connect, session resumption, graceful disconnect
* Error handling: mic permission denied, WebSocket failure → emit fallback event

### PR3: Frontend — UI integration + mode selection
* Mode selector on discover page: voice vs text
* Voice UI: mic button (start/stop), speaking state indicator, audio visualizer (simple)
* Display transcripts in chat panel during voice mode
* Auto-fallback to text mode on voice failure with error toast/message
* Existing text chat unchanged (no regression)
* Taste profile + recommendation panels work identically in both modes

### PR4: Voice system prompt + integration testing
* Craft voice-specific discovery system prompt for Gemini (adapted from current Claude prompt)
* End-to-end integration: voice conversation → transcript → persona pipeline → product recommendations update
* Test failure scenarios: disconnect, mic denied, slow persona pipeline
* Polish and edge case fixes

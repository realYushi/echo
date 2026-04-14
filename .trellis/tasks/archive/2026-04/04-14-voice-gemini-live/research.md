# Gemini Live API — Research Findings

> Research conducted 2026-04-14 for Echo voice-first taste discovery feature.
> Approach: **Raw WebSockets** (no SDK). No mid-session persona injection.
> Source: [Official WebSocket guide](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket)

---

## 1. Connection & Authentication

### Direct API Key (dev/testing)

```
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=API_KEY
```

### Ephemeral Tokens (production — browser-safe)

```
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained?access_token={token}
```

Note: ephemeral tokens require `v1alpha` endpoint.

### Session Setup

First message over the WebSocket must be `BidiGenerateContentSetup`:

```javascript
const configMessage = {
  config: {
    model: "models/gemini-3.1-flash-live-preview",
    responseModalities: ["AUDIO"],
    systemInstruction: {
      parts: [{ text: "You are Echo, a taste discovery assistant..." }]
    }
  }
};
websocket.send(JSON.stringify(configMessage));
```

---

## 2. Message Protocol

All messages are JSON conforming to `BidiGenerateContentClientMessage` (client→server) and `BidiGenerateContentServerMessage` (server→client).

### Sending Audio (client → server)

```javascript
const audioMessage = {
  realtimeInput: {
    audio: {
      data: base64EncodedPCM,     // 16-bit PCM, 16kHz, little-endian, mono
      mimeType: "audio/pcm;rate=16000"
    }
  }
};
websocket.send(JSON.stringify(audioMessage));
```

### Sending Text (client → server)

```javascript
const textMessage = {
  realtimeInput: { text: "Hello, how are you?" }
};
websocket.send(JSON.stringify(textMessage));
```

### Receiving Responses (server → client)

```javascript
websocket.onmessage = (event) => {
  const response = JSON.parse(event.data);

  if (response.serverContent) {
    const sc = response.serverContent;

    // Audio output (base64 PCM 24kHz)
    if (sc.modelTurn?.parts) {
      for (const part of sc.modelTurn.parts) {
        if (part.inlineData) {
          // part.inlineData.data = base64 PCM audio
          // Decode and queue for playback
        }
      }
    }

    // Transcripts
    if (sc.inputTranscription) {
      // User said: sc.inputTranscription.text
    }
    if (sc.outputTranscription) {
      // Gemini said: sc.outputTranscription.text
    }

    // Turn boundaries
    if (sc.turnComplete) {
      // Good time to send accumulated transcripts to backend
    }
    if (sc.interrupted) {
      // User interrupted — stop audio playback
    }
  }

  // Tool calls (if configured)
  if (response.toolCall) {
    // Handle function calls
  }
};
```

---

## 3. Browser Audio Pipeline

### Audio Capture (Mic → Gemini)

1. `navigator.mediaDevices.getUserMedia({ audio: true })` → `MediaStream`
2. `AudioContext` + `AudioWorkletNode` for PCM extraction
3. Format: **16-bit PCM, 16kHz, mono, little-endian**
4. Base64-encode each chunk, send as `realtimeInput.audio`
5. Chunk size: ~512 samples at 16kHz (32ms). Recommended: 20-40ms chunks.

### Audio Playback (Gemini → Speakers)

1. `AudioContext` at **24kHz** output sample rate
2. `AudioWorkletNode` for glitch-free playback
3. Decode base64 → Int16Array → Float32Array, queue as `AudioBuffer`

### Echo Cancellation

None built-in. Options:
- Headphones for MVP
- `echoCancellation: true` constraint on `getUserMedia` (browser-dependent)
- WebRTC/LiveKit for production (out of scope)

### Safari Gotcha

`AudioContext` created in `suspended` state. Must `resume()` via user gesture (e.g., mic button click).

---

## 4. Transcript Flow (key for persona pipeline)

### Configuration

Transcription is enabled in the setup config:

```javascript
config: {
  model: "models/gemini-3.1-flash-live-preview",
  responseModalities: ["AUDIO"],
  inputAudioTranscription: { languageCodes: ["en-US"] },
  outputAudioTranscription: { languageCodes: ["en-US"] },
  systemInstruction: { parts: [{ text: "..." }] }
}
```

### Accumulation Strategy

Transcripts arrive as fragments. Accumulate per turn, send to backend on `turnComplete`:

```
inputTranscription fragments → accumulate → turnComplete → POST /voice/transcript
outputTranscription fragments → accumulate → display in chat panel
```

Backend receives transcript, fires async persona pipeline (Haiku → Sonnet → CLIP), updates product recommendations.

---

## 5. Ephemeral Tokens (Backend)

### Python — using `google-genai` package

```python
from google import genai
from datetime import datetime, timedelta, timezone

client = genai.Client(http_options={"api_version": "v1alpha"})

now = datetime.now(timezone.utc)
token = client.auth_tokens.create(config={
    "uses": 1,
    "expire_time": (now + timedelta(minutes=30)).isoformat() + "Z",
    "new_session_expire_time": (now + timedelta(minutes=2)).isoformat() + "Z",
    "live_connect_constraints": {
        "model": "gemini-3.1-flash-live-preview",
        "config": {"response_modalities": ["AUDIO"]}
    },
    "http_options": {"api_version": "v1alpha"},
})
# token.name = the ephemeral token string to return to frontend
```

### Critical Gotchas

1. **`v1alpha` required on BOTH backend (token creation) and frontend (WS endpoint)**
2. `uses: 1` still allows reconnects within the same session
3. `new_session_expire_time` default is 1 minute — set to 2+ minutes
4. `expire_time` max is 30 minutes — generate new token for longer sessions

### FastAPI Endpoint

```python
@router.post("/voice/token")
async def create_voice_token(settings: Settings = Depends(get_settings)):
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1alpha"}
    )
    now = datetime.now(timezone.utc)
    token = client.auth_tokens.create(config={...})
    return {"token": token.name}
```

---

## 6. Session Management

| Scenario | Limit |
|----------|-------|
| Audio-only, no compression | ~15 minutes |
| With compression + resumption | Effectively unlimited |
| WebSocket connection lifetime | ~10 minutes (server resets) |

Audio ≈ 25 tokens/second → 128k context fills in ~85 min without compression.

### Compression Config (in setup message)

```javascript
contextWindowCompression: {
  triggerTokens: 50000,
  slidingWindow: { targetTokens: 4000 }
}
```

### Session Resumption

```javascript
// Enable in setup config
sessionResumption: {}  // empty = new session

// During session, store handles
if (message.sessionResumptionUpdate?.resumable) {
  savedHandle = message.sessionResumptionUpdate.newHandle;
}

// Reconnect with handle after disconnect
sessionResumption: { handle: savedHandle }
```

- Handles valid for **2 hours** after session termination
- Server sends `GoAway` ~60s before disconnecting — listen for it
- `resumable` may be `false` during active generation — only reconnect when `true`

---

## 7. Architecture Summary for Echo

```
Browser                                    Backend
┌──────────────────────┐
│  [🎤 Start Voice]    │
│  getUserMedia()      │
│  AudioWorklet (PCM)  │
└────────┬─────────────┘
         │ raw WebSocket (JSON + base64 PCM)
         ▼
   Gemini Live API ◄─── system prompt (persona discovery)
   (speech-to-speech)      set once at session start
         │
         ├── audio output ──► AudioWorklet ──► speakers
         ├── inputTranscription ──► chat panel (user turns)
         ├── outputTranscription ──► chat panel (agent turns)
         └── turnComplete ──► POST /voice/transcript ──► Backend
                                                            │
                                                   Haiku → Sonnet → CLIP
                                                            │
                                                   persona update (SSE)
                                                            │
                                              ┌─────────────┴──────────┐
                                              ▼                        ▼
                                    taste profile panel     product recommendations
```

### Key Design Decisions

1. **Raw WebSockets, no SDK** — full control, simple JSON protocol, lighter bundle
2. **No mid-session injection** — Gemini's conversation history handles personalization naturally
3. **Persona pipeline feeds recommendations only** — not fed back into Gemini
4. **Ephemeral tokens** — API key never exposed to browser
5. **Model**: `gemini-3.1-flash-live-preview`

### Dependencies

**Backend**: `google-genai` Python package (for ephemeral token creation only)
**Frontend**: No Gemini SDK — raw `WebSocket` API + Web Audio API (`AudioWorklet`)

---

## 8. Reference

- [WebSocket getting started](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket)
- [Live API capabilities](https://ai.google.dev/gemini-api/docs/live-guide)
- [Session management](https://ai.google.dev/gemini-api/docs/live-session)
- [Ephemeral tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens)
- [WebSocket API reference](https://ai.google.dev/api/live)
- [Example app (ephemeral tokens + WebSocket)](https://github.com/google-gemini/gemini-live-api-examples/tree/main/gemini-live-ephemeral-tokens-websocket)

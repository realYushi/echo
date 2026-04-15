# Add Frontend Logger

## Goal

Add structured logging to the Next.js frontend so errors, API failures, and key user interactions are captured in a consistent, queryable format — matching the structured logging discipline already in the backend.

## Requirements

- Single logger instance used across all frontend modules
- Structured log output (JSON objects) via Pino
- Child loggers per module (e.g., `logger.child({ module: "useVoiceChat" })`)
- All API call errors logged with status codes and context
- Voice hook logs connection lifecycle events (connect, disconnect, errors, fallback)
- Chat hook logs streaming errors
- SSE stream parse errors logged
- React error boundary catches and logs rendering crashes
- X-Request-ID sent on API calls; logs include it for cross-stack correlation
- `typeof window` SSR guard since all usage is in `"use client"` components

## Acceptance Criteria

- [ ] `pino` added as dependency
- [ ] Logger module created at `src/lib/logger.ts` with Pino browser config
- [ ] Child loggers exported for each module (or factory function)
- [ ] `src/lib/api.ts` — all fetch error paths log before throwing
- [ ] `src/lib/sse.ts` — stream parse errors logged
- [ ] `src/hooks/useChat.ts` — streaming errors logged
- [ ] `src/hooks/useVoiceChat.ts` — connect, disconnect, WebSocket errors, fallback logged
- [ ] `src/hooks/usePersona.ts` — feedback errors logged
- [ ] `src/hooks/useRecommendations.ts` — fetch errors logged
- [ ] `src/app/discover/page.tsx` — hydration errors logged
- [ ] Error boundary component created, wrapping the discover page
- [ ] X-Request-ID generated per session, sent on API calls, included in logs
- [ ] Lint, typecheck, all existing tests pass
- [ ] Logger module has unit tests

## Definition of Done

- `make lint` and `make test` green (both backend and frontend)
- All existing tests still pass with no regressions
- No new warnings introduced

## Technical Approach

**Library**: Pino (full) with `browser.asObject: true`

**Logger module** (`src/lib/logger.ts`):
- Creates root Pino instance with browser config
- Exports `createLogger(module: string)` factory that returns child loggers
- SSR guard: returns no-op logger when `typeof window === "undefined"`
- Includes `sessionId` and `requestId` in log context

**X-Request-ID**:
- Generate a session-level request ID prefix in `src/lib/logger.ts`
- Pass via `X-Request-ID` header on all fetch calls in `api.ts`
- Include in all log entries so backend and frontend logs can be correlated

**Error boundary**:
- React error boundary component in `src/components/ErrorBoundary.tsx`
- Logs the error via the logger, renders a fallback UI
- Wraps the discover page content

**Integration pattern**:
Each hook/module creates its own child logger:
```ts
const logger = createLogger("useVoiceChat");
```
Then in catch blocks:
```ts
logger.error({ err, sessionId }, "voice_ws_error");
```

## Out of Scope

- Remote logging service integration (Sentry, Datadog, etc.)
- Backend endpoint to receive frontend logs
- Log shipping/batching
- Production log level configuration via env

## Technical Notes

### Files to modify
- `frontend/package.json` — add pino dependency
- `frontend/src/lib/logger.ts` — NEW: logger module
- `frontend/src/lib/api.ts` — add X-Request-ID header, log errors
- `frontend/src/lib/sse.ts` — log parse errors
- `frontend/src/hooks/useChat.ts` — log streaming errors
- `frontend/src/hooks/useVoiceChat.ts` — log lifecycle events
- `frontend/src/hooks/usePersona.ts` — log feedback errors
- `frontend/src/hooks/useRecommendations.ts` — log fetch errors
- `frontend/src/app/discover/page.tsx` — log hydration errors, wrap with error boundary
- `frontend/src/components/ErrorBoundary.tsx` — NEW: error boundary component

### Decision (ADR-lite)
**Context**: Frontend has zero observability — errors vanish when UI state resets.
**Decision**: Pino with browser mode, child loggers, X-Request-ID correlation, React error boundary.
**Consequences**: ~8KB gzipped added to bundle. All future frontend errors become traceable. Backend and frontend logs can be correlated via request ID.

# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

TypeScript strict mode. ESLint + Prettier. Vitest for testing.

---

## Forbidden Patterns

| Pattern | Why | Instead |
|---------|-----|---------|
| `any` type | Defeats type checking | Proper types or `unknown` |
| `useEffect` for derived state | Unnecessary re-renders, stale bugs | Compute during render |
| `<div onClick>` for interactive elements | Accessibility | `<button>` or `<a>` |
| Inline styles | Inconsistent, not responsive | Tailwind classes |
| `console.log` in committed code | Noise in production | Remove or use a logger |
| Index as key for dynamic lists | Re-render bugs | Use stable IDs |
| Barrel exports (`index.ts` re-exporting everything) | Slow bundling, circular deps | Import directly from the file |

---

## Required Patterns

- **Strict TypeScript** — `"strict": true` in `tsconfig.json`, zero `any`
- **Named exports** — `export function Component()`, not `export default`
- **Error boundaries** — wrap major sections to prevent full-page crashes
- **Loading/error states** — every async operation shows feedback to the user
- **Tailwind** — all styling via utility classes

---

## Testing Requirements

- **Framework**: Vitest + React Testing Library
- **What to test**:
  - Custom hooks (useChat, usePersona, useRecommendations) — these hold the business logic
  - Utility functions in `lib/`
  - Component interaction behavior (click feedback button → callback fires)
- **What not to test**:
  - Static rendering of pure display components
  - Tailwind class names
  - Next.js routing (tested by the framework)
- **Test naming**: `{feature}.test.ts` co-located or in `__tests__/`

```tsx
import { renderHook, act } from "@testing-library/react";
import { usePersona } from "@/hooks/usePersona";

test("updates persona when new signals arrive", () => {
  const { result } = renderHook(() => usePersona(initialPersona));
  act(() => {
    result.current.addSignal({ type: "rejection", value: "rustic" });
  });
  expect(result.current.persona.rejections).toContain("rustic");
});
```

---

## Code Review Checklist

- [ ] No `any` types
- [ ] No `useEffect` for derived state
- [ ] Loading and error states handled
- [ ] Interactive elements are semantic HTML (`button`, `a`)
- [ ] Images have `alt` text
- [ ] SSE / fetch connections clean up on unmount
- [ ] New types added to `src/types/` if shared

---

## Tooling

- **Linter**: ESLint with `next/core-web-vitals` + TypeScript rules
- **Formatter**: Prettier
- **Test runner**: Vitest
- **Config**: `eslint.config.mjs`, `.prettierrc`, `vitest.config.ts`

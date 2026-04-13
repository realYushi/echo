# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

TypeScript strict mode. ESLint 9 (flat config) + Prettier 3. Vitest 3 for testing.

---

## Forbidden Patterns

| Pattern | Why | Instead |
|---------|-----|---------|
| `any` type | Defeats type checking | Proper types or `unknown` |
| `useEffect` for derived state | Unnecessary re-renders, stale bugs | Compute during render |
| `<div onClick>` for interactive elements | Accessibility | `<button>` or `<a>` |
| Inline styles | Inconsistent, not responsive | Tailwind classes |
| `console.log` in committed code | Noise in production | Remove or use a logger |
| Index as key for dynamic lists | Re-render bugs | Use stable IDs (see `RecommendationGrid.tsx:31` using `rec.product.id`) |
| Barrel exports (`index.ts` re-exporting everything) | Slow bundling, circular deps | Import directly from the file |
| `export default` for components | Inconsistent naming across imports | Named exports (`export function Component`) |

---

## Required Patterns

- **Strict TypeScript** -- `"strict": true` in `tsconfig.json:8`, zero `any`
- **Named exports** -- `export function Component()`, not `export default` (page components excepted)
- **Error boundaries** -- wrap major sections to prevent full-page crashes
- **Loading/error states** -- every async operation shows feedback to the user (see `RecommendationGrid.tsx` for loading/empty/populated pattern)
- **Tailwind** -- all styling via utility classes, conditional classes via `cn()` from `src/lib/utils.ts`
- **`"use client"` directive** -- required on any component that uses hooks, state, or event handlers
- **`import type`** -- use for type-only imports throughout
- **Explicit button semantics** -- shared UI button primitives default to `type="button"` unless submit behavior is intentional
- **Runtime-valid image strategy** -- if product/catalog media comes from remote SVG placeholder services, use `next/image` with `unoptimized` or a plain `<img>` after verifying the source actually works through the optimizer

---

## Testing Requirements

- **Framework**: Vitest 3 + React Testing Library 16
- **Config**: `vitest.config.ts` -- jsdom environment, globals enabled, `@/` alias for imports
- **TypeScript gotcha**: test files should import `describe`, `it`, `expect`, `vi`, and lifecycle helpers from `vitest` explicitly unless the project tsconfig includes Vitest types
- **What to test**:
  - Custom hooks (`useChat`, `usePersona`, `useRecommendations`) -- these hold the business logic
  - Utility functions in `lib/` (e.g., `cn()` in `utils.ts`)
  - Component interaction behavior (click feedback button -> callback fires)
- **What not to test**:
  - Static rendering of pure display components (e.g., `EmptyState`)
  - Tailwind class names
  - Next.js routing (tested by the framework)
- **Test naming**: `{feature}.test.ts` co-located or in `__tests__/`

**Vitest config** (`vitest.config.ts`):
```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
});
```

---

## Tooling Configuration

### ESLint (`eslint.config.mjs`)

ESLint 9 flat config format using `FlatCompat` to bridge the `next/core-web-vitals` and `next/typescript` configs:

```js
import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
];

export default eslintConfig;
```

### Prettier (`.prettierrc`)

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "tabWidth": 2,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

Key rules: semicolons, double quotes, trailing commas everywhere, 2-space indent, automatic Tailwind class sorting.

### TypeScript (`tsconfig.json`)

Key settings:
- `"strict": true` -- all strict checks enabled
- `"target": "ES2022"` / `"module": "nodenext"` -- modern JS output
- `"paths": { "@/*": ["./src/*"] }` -- path alias for clean imports
- `"noEmit": true` -- type checking only, Next.js handles compilation

---

## Verification Commands

Run from the `frontend/` directory:

```bash
# Type checking
npm run typecheck    # tsc --noEmit

# Linting
npm run lint         # next lint

# Tests
npm run test         # vitest
```

---

## Code Review Checklist

- [ ] No `any` types
- [ ] No `useEffect` for derived state
- [ ] Loading and error states handled
- [ ] Interactive elements are semantic HTML (`button`, `a`)
- [ ] Shared buttons do not accidentally submit enclosing forms
- [ ] Images have `alt` text
- [ ] Remote image strategy is runtime-tested if using `next/image`
- [ ] SSE / fetch connections clean up on unmount
- [ ] New types added to `src/types/` if shared
- [ ] `"use client"` directive present on components with hooks/handlers
- [ ] Named exports used for components (not `export default`)
- [ ] Props interface defined as `{Component}Props`
- [ ] `import type` used for type-only imports

---

## Reference Files

| Config | File |
|--------|------|
| TypeScript config | `tsconfig.json` |
| ESLint flat config | `eslint.config.mjs` |
| Prettier config | `.prettierrc` |
| Vitest config | `vitest.config.ts` |
| PostCSS / Tailwind v4 | `postcss.config.mjs` |
| Tailwind entry | `src/styles/globals.css` |
| Package scripts | `package.json` |

# Component Guidelines

> How components are built in this project.

---

## Overview

React functional components with TypeScript. Tailwind CSS for styling. No class components.

---

## Component Structure

Standard order within a component file:

```tsx
// 1. Imports
import { useState } from "react";
import type { Product } from "@/types/product";

// 2. Types (if component-local)
interface ProductCardProps {
  product: Product;
  onFeedback: (productId: string, signal: "like" | "dislike") => void;
}

// 3. Component
export function ProductCard({ product, onFeedback }: ProductCardProps) {
  // hooks first
  const [isHovered, setIsHovered] = useState(false);

  // handlers
  function handleLike() {
    onFeedback(product.id, "like");
  }

  // render
  return (
    <div className="rounded-lg border p-4">
      ...
    </div>
  );
}
```

---

## Props Conventions

- Define props as an `interface` named `{Component}Props` in the same file
- Destructure props in the function signature
- Use `children: React.ReactNode` for composition, not custom render props
- Event handlers: `on{Event}` naming (`onFeedback`, `onSend`, `onClose`)

```tsx
// Good: explicit interface
interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

// Bad: inline types
function ChatInput({ onSend, disabled }: { onSend: (m: string) => void; disabled?: boolean }) { ... }
```

---

## Styling Patterns

- **Tailwind CSS** for all styling
- Use `cn()` helper (from `clsx` + `tailwind-merge`) for conditional classes
- No CSS modules or styled-components
- Responsive: desktop-first (the discovery UI is desktop-only for MVP)

```tsx
import { cn } from "@/lib/utils";

<div className={cn("rounded-lg border", isActive && "border-blue-500")} />
```

---

## Accessibility

- Interactive elements must be `<button>` or `<a>`, not `<div onClick>`
- Images require `alt` text
- Form inputs require associated labels
- Focus management for the chat input after message send

---

## Common Mistakes

- **Don't put business logic in components** — extract to hooks or `lib/`
- **Don't use `useEffect` for derived state** — compute during render
- **Don't create wrapper components that just pass props through** — compose directly

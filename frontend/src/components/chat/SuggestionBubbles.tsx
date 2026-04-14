"use client";

import { Button } from "@/components/ui/Button";

interface SuggestionBubblesProps {
  suggestions: string[];
  onSelect: (suggestion: string) => Promise<void> | void;
  disabled: boolean;
}

export function SuggestionBubbles({
  suggestions,
  onSelect,
  disabled,
}: SuggestionBubblesProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-[color:var(--line)] bg-[color:var(--panel)]/65 px-4 py-3 sm:px-5">
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <Button
            key={suggestion}
            variant="secondary"
            disabled={disabled}
            className="rounded-full border-[color:var(--line)] bg-white/85 px-4 py-2 text-xs tracking-[0.02em] text-[color:var(--ink)]"
            onClick={() => {
              void onSelect(suggestion);
            }}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  );
}

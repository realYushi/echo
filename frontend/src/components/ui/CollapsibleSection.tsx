"use client";

import { useId, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
  headerRight?: ReactNode;
}

export function CollapsibleSection({
  title,
  defaultOpen,
  children,
  className,
  headerRight,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState<boolean>(defaultOpen ?? false);
  const bodyId = useId();

  return (
    <div
      className={cn(
        "overflow-hidden rounded-[20px] border border-[color:var(--line)] bg-[color:var(--panel)]/80",
        className,
      )}
    >
      <div className="flex items-center gap-2 px-4 py-3">
        <button
          type="button"
          aria-expanded={isOpen}
          aria-controls={bodyId}
          onClick={() => setIsOpen((prev) => !prev)}
          className="flex flex-1 items-center gap-2 text-left text-sm font-medium text-[color:var(--ink)] transition-colors hover:text-[color:var(--ink)]/80"
        >
          <span
            aria-hidden="true"
            className={cn(
              "inline-block text-[color:var(--muted)] transition-transform duration-150",
              isOpen ? "rotate-90" : "rotate-0",
            )}
          >
            &rsaquo;
          </span>
          <span className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
            {title}
          </span>
        </button>
        {headerRight ? (
          <div className="flex shrink-0 items-center">{headerRight}</div>
        ) : null}
      </div>
      <div
        id={bodyId}
        hidden={!isOpen}
        className="border-t border-[color:var(--line)] bg-white/60 px-4 py-3"
      >
        {children}
      </div>
    </div>
  );
}

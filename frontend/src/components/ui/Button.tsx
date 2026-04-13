"use client";

import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

export function Button({
  variant = "primary",
  className,
  children,
  type,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type ?? "button"}
      className={cn(
        "rounded-xl px-4 py-2 font-medium transition duration-200 disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" &&
          "bg-[color:var(--ink)] text-white shadow-[0_18px_32px_rgba(29,42,34,0.18)] hover:bg-[color:var(--ink)]/92",
        variant === "secondary" &&
          "border border-[color:var(--line)] bg-white text-[color:var(--ink)] hover:border-[color:var(--accent)]/30 hover:bg-[color:var(--accent-soft)]/35",
        variant === "ghost" &&
          "border border-transparent bg-transparent text-[color:var(--muted)] hover:border-[color:var(--line)] hover:bg-white/70 hover:text-[color:var(--ink)]",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

"use client";

import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

export function Button({ variant = "primary", className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "rounded-lg px-4 py-2 font-medium transition-colors disabled:opacity-50",
        variant === "primary" && "bg-gray-900 text-white hover:bg-gray-800",
        variant === "secondary" && "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50",
        variant === "ghost" && "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

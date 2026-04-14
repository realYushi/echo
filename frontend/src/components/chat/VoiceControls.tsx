"use client";

import { cn } from "@/lib/utils";

interface VoiceControlsProps {
  isConnected: boolean;
  isConnecting: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function VoiceControls({
  isConnected,
  isConnecting,
  onConnect,
  onDisconnect,
}: VoiceControlsProps) {
  const idle = !isConnected && !isConnecting;

  return (
    <div className="border-t border-[color:var(--line)] bg-[color:var(--panel)]/90 px-4 py-4 sm:px-5">
      <div className="flex flex-col items-center gap-3">
        <button
          type="button"
          disabled={isConnecting}
          onClick={isConnected ? onDisconnect : onConnect}
          className={cn(
            "flex h-14 w-14 items-center justify-center rounded-full transition duration-200",
            idle &&
              "border border-[color:var(--line)] bg-white text-[color:var(--muted)] hover:border-[color:var(--accent)]/30 hover:bg-[color:var(--accent-soft)]/35 hover:text-[color:var(--ink)]",
            isConnecting &&
              "animate-pulse border border-[color:var(--line)] bg-white text-[color:var(--muted)] cursor-not-allowed",
            isConnected &&
              "bg-[color:var(--accent)] text-white shadow-[0_0_0_8px_rgba(46,106,79,0.15)]",
          )}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-6 w-6"
          >
            <rect x="9" y="1" width="6" height="12" rx="3" />
            <path d="M5 10a7 7 0 0 0 14 0" />
            <line x1="12" y1="17" x2="12" y2="21" />
            <line x1="8" y1="21" x2="16" y2="21" />
          </svg>
        </button>
        <p className="text-xs text-[color:var(--muted)]">
          {idle && "Tap to start voice chat"}
          {isConnecting && "Connecting..."}
          {isConnected && "Listening\u2026 tap to stop"}
        </p>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, type ReactNode } from "react";
import type { Message } from "@/types/chat";
import { ChatInput } from "@/components/chat/ChatInput";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { SuggestionBubbles } from "@/components/chat/SuggestionBubbles";
import { cn } from "@/lib/utils";

interface ChatPanelProps {
  messages: Message[];
  suggestions: string[];
  onSend: (message: string) => Promise<void> | void;
  onSuggestionSelect: (message: string) => Promise<void> | void;
  isStreaming: boolean;
  inputDisabled?: boolean;
  statusLabel?: string;
  error: string | null;
  mode?: "text" | "voice";
  voiceSlot?: ReactNode;
}

export function ChatPanel({
  messages,
  suggestions,
  onSend,
  onSuggestionSelect,
  isStreaming,
  inputDisabled,
  statusLabel,
  error,
  mode = "text",
  voiceSlot,
}: ChatPanelProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isStreaming, messages]);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-[color:var(--line)] px-5 py-5 sm:px-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
              Guided Discovery
            </p>
            <h2 className="mt-2 text-2xl text-[color:var(--ink)]">
              Shape the shortlist out loud.
            </h2>
            <p className="mt-2 max-w-xl text-sm text-[color:var(--muted)]">
              Tell Echo what feels right, what feels wrong, and what the project
              needs. Each turn sharpens the recommendation set.
            </p>
          </div>
          <span
            className={cn(
              "rounded-full border px-3 py-1 text-[11px] font-medium tracking-[0.18em] uppercase",
              isStreaming || mode === "voice"
                ? "border-[color:var(--accent)]/30 bg-[color:var(--accent)]/10 text-[color:var(--accent)]"
                : "border-[color:var(--line)] bg-white/80 text-[color:var(--muted)]",
            )}
          >
            {statusLabel ??
              (mode === "voice"
                ? "Voice"
                : isStreaming
                  ? "Responding"
                  : "Ready")}
          </span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
        {messages.length === 0 && mode === "voice" ? (
          <div className="rounded-[28px] border border-dashed border-[color:var(--line)] bg-white/55 p-6 text-[color:var(--muted)]">
            <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
              Voice discovery
            </p>
            <p className="mt-4 text-sm leading-6">
              Tap the microphone below to start a voice conversation with Echo.
              Your words will appear here as the conversation flows.
            </p>
          </div>
        ) : messages.length === 0 ? (
          <div className="rounded-[28px] border border-dashed border-[color:var(--line)] bg-white/55 p-6 text-[color:var(--muted)]">
            <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
              Try prompts like
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-6">
              <li>
                &ldquo;I want a warm kitchen that feels architectural, not
                rustic.&rdquo;
              </li>
              <li>
                &ldquo;Show me statement lighting, but nothing overly
                glossy.&rdquo;
              </li>
              <li>
                &ldquo;I like natural stone and oak, but avoid anything too
                ornate.&rdquo;
              </li>
            </ul>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        )}

        {error ? (
          <div className="mt-4 rounded-[22px] border border-amber-300/60 bg-amber-50/80 px-4 py-3 text-sm text-amber-900">
            {error}
          </div>
        ) : null}

        <div ref={endRef} />
      </div>
      {mode === "voice" ? (
        voiceSlot
      ) : (
        <>
          <SuggestionBubbles
            suggestions={suggestions}
            onSelect={onSuggestionSelect}
            disabled={inputDisabled ?? isStreaming}
          />
          <ChatInput onSend={onSend} disabled={inputDisabled ?? isStreaming} />
        </>
      )}
    </div>
  );
}

"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";

interface ChatInputProps {
  onSend: (message: string) => Promise<void> | void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) {
      return;
    }

    setInput("");
    void onSend(trimmed);
    inputRef.current?.focus();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-[color:var(--line)] bg-[color:var(--panel)]/90 px-4 py-4 sm:px-5"
    >
      <label htmlFor="chat-input" className="sr-only">
        Describe what you want to discover
      </label>
      <div className="flex items-center gap-3 rounded-[24px] border border-[color:var(--line)] bg-white/90 p-2 shadow-[0_16px_40px_rgba(29,42,34,0.08)]">
        <input
          ref={inputRef}
          id="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe a room, react to a look, or say what to avoid..."
          disabled={disabled}
          className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-[color:var(--ink)] outline-none placeholder:text-[color:var(--muted)]/70 disabled:cursor-not-allowed"
        />
        <Button
          type="submit"
          disabled={disabled || !input.trim()}
          className="min-w-[6.5rem] rounded-[18px] px-5 py-3 text-sm"
        >
          {disabled ? "Thinking" : "Send"}
        </Button>
      </div>
    </form>
  );
}

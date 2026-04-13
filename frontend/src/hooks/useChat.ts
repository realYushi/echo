"use client";

import { useState, useCallback } from "react";
import type { Message } from "@/types/chat";

interface UseChatReturn {
  messages: Message[];
  sendMessage: (content: string) => void;
  isStreaming: boolean;
  error: string | null;
}

export function useChat(_sessionId: string): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback((content: string) => {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content }]);

    // TODO: Wire up SSE streaming via lib/sse.ts
    // For now, add a placeholder assistant response
    setIsStreaming(true);
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "This is a placeholder response. Chat streaming will be implemented in a later PR.",
        },
      ]);
      setIsStreaming(false);
    }, 500);
  }, []);

  return { messages, sendMessage, isStreaming, error };
}

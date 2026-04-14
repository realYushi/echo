"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat } from "@/lib/sse";
import type { ChatRequest, Message } from "@/types/chat";
import type { Persona } from "@/types/persona";

interface UseChatOptions {
  persona: Persona | null;
  onPersonaUpdate: (persona: Persona) => void;
  onTurnComplete?: () => Promise<void> | void;
}

interface UseChatReturn {
  messages: Message[];
  suggestions: string[];
  replaceMessages: (messages: Message[]) => void;
  sendMessage: (content: string) => Promise<void>;
  isStreaming: boolean;
  error: string | null;
}

function createMessage(role: Message["role"], content: string): Message {
  return {
    id: crypto.randomUUID(),
    role,
    content,
  };
}

function appendAssistantContent(
  messages: Message[],
  content: string,
): Message[] {
  const lastMessage = messages.at(-1);
  if (lastMessage?.role === "assistant") {
    return [
      ...messages.slice(0, -1),
      {
        ...lastMessage,
        content: `${lastMessage.content}${content}`,
      },
    ];
  }

  return [...messages, createMessage("assistant", content)];
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to reach Echo right now. Please try again.";
}

export function useChat(
  sessionId: string,
  options: UseChatOptions,
): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const { persona, onPersonaUpdate, onTurnComplete } = options;

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    abortControllerRef.current?.abort();
    setMessages([]);
    setSuggestions([]);
    setIsStreaming(false);
    setError(null);
  }, [sessionId]);

  const replaceMessages = useCallback((nextMessages: Message[]) => {
    setError(null);
    setMessages(nextMessages);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!sessionId || !trimmed || isStreaming) {
        return;
      }

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setError(null);
      setSuggestions([]);
      setMessages((prev) => [...prev, createMessage("user", trimmed)]);
      setIsStreaming(true);

      let streamErrored = false;
      let receivedAssistantContent = false;

      try {
        const request: ChatRequest = {
          sessionId,
          message: trimmed,
          persona,
        };

        await streamChat(
          request,
          (event) => {
            switch (event.type) {
              case "token":
                receivedAssistantContent = true;
                setMessages((prev) =>
                  appendAssistantContent(prev, event.content),
                );
                return;
              case "suggestions":
                setSuggestions(event.suggestions);
                return;
              case "persona_update":
                onPersonaUpdate(event.persona);
                return;
              case "error":
                streamErrored = true;
                setError(event.message);
                if (!receivedAssistantContent) {
                  setMessages((prev) =>
                    appendAssistantContent(prev, event.message),
                  );
                }
                return;
              case "done":
                return;
            }
          },
          controller.signal,
        );

        if (!streamErrored) {
          await onTurnComplete?.();
        }
      } catch (nextError) {
        if (isAbortError(nextError)) {
          return;
        }

        const message = getErrorMessage(nextError);
        setError(message);
        setSuggestions([]);
        if (!receivedAssistantContent) {
          setMessages((prev) => appendAssistantContent(prev, message));
        }
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
        setIsStreaming(false);
      }
    },
    [isStreaming, onPersonaUpdate, onTurnComplete, persona, sessionId],
  );

  return {
    messages,
    suggestions,
    replaceMessages,
    sendMessage,
    isStreaming,
    error,
  };
}

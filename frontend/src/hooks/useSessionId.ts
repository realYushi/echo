"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "echo.discovery.session-id";

interface UseSessionIdReturn {
  sessionId: string | null;
  isReady: boolean;
  startNewSession: () => void;
}

function createSessionId(): string {
  return crypto.randomUUID();
}

function readStoredSessionId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const storedValue = window.localStorage.getItem(STORAGE_KEY)?.trim();
  return storedValue ? storedValue : null;
}

function persistSessionId(sessionId: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, sessionId);
}

export function useSessionId(): UseSessionIdReturn {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    const nextSessionId = readStoredSessionId() ?? createSessionId();
    persistSessionId(nextSessionId);
    setSessionId(nextSessionId);
  }, []);

  const startNewSession = useCallback(() => {
    const nextSessionId = createSessionId();
    persistSessionId(nextSessionId);
    setSessionId(nextSessionId);
  }, []);

  return {
    sessionId,
    isReady: sessionId !== null,
    startNewSession,
  };
}

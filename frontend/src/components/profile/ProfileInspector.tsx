"use client";

import { useEffect, useMemo, useState } from "react";
import { CollapsibleSection } from "@/components/ui/CollapsibleSection";
import { cn } from "@/lib/utils";
import type { Message } from "@/types/chat";
import type { Persona } from "@/types/persona";
import type { Recommendation } from "@/types/product";

const DEV_MODE_STORAGE_KEY = "echo.profile-inspector.dev-mode";

interface ChatStateSlice {
  messages: Message[];
  suggestions: string[];
  isStreaming: boolean;
  error: string | null;
}

interface ProfileInspectorProps {
  persona: Persona;
  recommendations: Recommendation[];
  chatState: ChatStateSlice;
  sessionId: string;
  isHydrating: boolean;
}

function readStoredDevMode(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const storedValue = window.localStorage.getItem(DEV_MODE_STORAGE_KEY);
  return storedValue === "true";
}

function persistDevMode(value: boolean): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(DEV_MODE_STORAGE_KEY, value ? "true" : "false");
}

function Chip({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "positive" | "negative";
}) {
  return (
    <span
      className={cn(
        "rounded-full border px-2.5 py-1 text-xs text-[color:var(--ink)]",
        tone === "positive" &&
          "border-[color:var(--accent)]/25 bg-[color:var(--accent-soft)]/40",
        tone === "negative" && "border-red-200 bg-red-50/60",
        tone === "neutral" &&
          "border-[color:var(--line)] bg-[color:var(--accent-soft)]/55",
      )}
    >
      {children}
    </span>
  );
}

function EmptyHint({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-[color:var(--muted)]">{children}</p>;
}

function RawJson({ value }: { value: unknown }) {
  return (
    <pre className="max-h-64 overflow-auto rounded-lg border border-[color:var(--line)] bg-[color:var(--panel)] p-3 font-mono text-[11px] leading-5 text-[color:var(--ink)]">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export function ProfileInspector({
  persona,
  recommendations,
  chatState,
  sessionId,
  isHydrating,
}: ProfileInspectorProps) {
  const [devMode, setDevMode] = useState<boolean>(false);

  useEffect(() => {
    setDevMode(readStoredDevMode());
  }, []);

  function toggleDevMode() {
    setDevMode((prev) => {
      const next = !prev;
      persistDevMode(next);
      return next;
    });
  }

  const productNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const rec of recommendations) {
      map.set(rec.product.id, rec.product.name);
    }
    return map;
  }, [recommendations]);

  function resolveProductLabel(productId: string): string {
    return productNameById.get(productId) ?? productId;
  }

  const messageCount = chatState.messages.length;
  const lastMessageRole = chatState.messages.at(-1)?.role ?? "—";
  const statusLabel = isHydrating
    ? "Hydrating…"
    : chatState.isStreaming
      ? "Streaming…"
      : "Idle";
  const sessionLabel = sessionId ? sessionId.slice(0, 8) : "—";

  return (
    <section className="rounded-[32px] border border-[color:var(--line)] bg-white/70 p-5 shadow-[0_24px_60px_rgba(29,42,34,0.08)] backdrop-blur-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
            Taste profile
          </p>
          <h2 className="mt-2 text-2xl text-[color:var(--ink)]">
            Signals coming into focus.
          </h2>
          <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
            Echo updates this profile as the conversation evolves, then uses it
            to reshape the shortlist in real time.
          </p>
        </div>
        <button
          type="button"
          onClick={toggleDevMode}
          aria-pressed={devMode}
          className={cn(
            "rounded-full border px-3 py-2 text-[11px] tracking-[0.16em] uppercase transition-colors",
            devMode
              ? "border-[color:var(--ink)] bg-[color:var(--ink)] text-white"
              : "border-[color:var(--line)] bg-white/80 text-[color:var(--muted)] hover:bg-[color:var(--accent-soft)]/40",
          )}
        >
          Developer mode {devMode ? "on" : "off"}
        </button>
      </div>

      <div className="mt-5 flex flex-col gap-2">
        <CollapsibleSection title="Budget & direction">
          {persona.budgetTier ? (
            <div className="flex flex-wrap gap-2">
              <Chip>{persona.budgetTier}</Chip>
            </div>
          ) : (
            <EmptyHint>Not set yet.</EmptyHint>
          )}
        </CollapsibleSection>

        <CollapsibleSection title="Likes">
          {persona.likes.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {persona.likes.map((item) => (
                <Chip key={item} tone="positive">
                  {item}
                </Chip>
              ))}
            </div>
          ) : (
            <EmptyHint>Positive signals will show up here.</EmptyHint>
          )}
        </CollapsibleSection>

        <CollapsibleSection title="Dislikes">
          {persona.hates.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {persona.hates.map((item) => (
                <Chip key={item} tone="negative">
                  {item}
                </Chip>
              ))}
            </div>
          ) : (
            <EmptyHint>Dislikes help Echo steer away faster.</EmptyHint>
          )}
        </CollapsibleSection>

        <CollapsibleSection title="Approved products">
          {persona.approvals.length > 0 ? (
            <ul className="flex flex-col gap-1.5 text-sm text-[color:var(--ink)]">
              {persona.approvals.map((productId) => (
                <li key={productId} className="flex items-baseline gap-2">
                  <span className="text-xs text-[color:var(--muted)]">
                    {productId.slice(0, 8)}
                  </span>
                  <span>{resolveProductLabel(productId)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyHint>No approvals yet.</EmptyHint>
          )}
        </CollapsibleSection>

        <CollapsibleSection title="Rejected products">
          {persona.rejections.length > 0 ? (
            <ul className="flex flex-col gap-1.5 text-sm text-[color:var(--ink)]">
              {persona.rejections.map((productId) => (
                <li key={productId} className="flex items-baseline gap-2">
                  <span className="text-xs text-[color:var(--muted)]">
                    {productId.slice(0, 8)}
                  </span>
                  <span>{resolveProductLabel(productId)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyHint>No rejections yet.</EmptyHint>
          )}
        </CollapsibleSection>

        <CollapsibleSection title="Session summary">
          <dl className="grid grid-cols-1 gap-2 text-sm text-[color:var(--ink)] sm:grid-cols-3">
            <div>
              <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                Session
              </dt>
              <dd className="mt-1 font-mono text-xs">{sessionLabel}</dd>
            </div>
            <div>
              <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                Messages
              </dt>
              <dd className="mt-1">{messageCount}</dd>
            </div>
            <div>
              <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                Status
              </dt>
              <dd className="mt-1">{statusLabel}</dd>
            </div>
          </dl>
        </CollapsibleSection>

        {devMode && (
          <>
            <CollapsibleSection title="Raw persona JSON">
              <RawJson value={persona} />
            </CollapsibleSection>

            <CollapsibleSection title="Recommendations with scores">
              {recommendations.length > 0 ? (
                <ul className="flex flex-col gap-1.5 font-mono text-xs text-[color:var(--ink)]">
                  {recommendations.map((rec) => (
                    <li key={rec.product.id}>
                      <span className="text-[color:var(--muted)]">
                        {rec.product.id.slice(0, 8)}
                      </span>
                      <span> — </span>
                      <span>{rec.product.name}</span>
                      <span> — </span>
                      <span>{rec.score.toFixed(3)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyHint>None right now.</EmptyHint>
              )}
            </CollapsibleSection>

            <CollapsibleSection title="Assistant suggestions">
              {chatState.suggestions.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {chatState.suggestions.map((suggestion) => (
                    <Chip key={suggestion}>{suggestion}</Chip>
                  ))}
                </div>
              ) : (
                <EmptyHint>None right now.</EmptyHint>
              )}
            </CollapsibleSection>

            <CollapsibleSection title="Live chat state">
              <dl className="grid grid-cols-1 gap-2 text-sm text-[color:var(--ink)] sm:grid-cols-2">
                <div>
                  <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                    Streaming
                  </dt>
                  <dd className="mt-1 font-mono text-xs">
                    {chatState.isStreaming ? "true" : "false"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                    Error
                  </dt>
                  <dd className="mt-1 font-mono text-xs break-words">
                    {chatState.error ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                    Last message role
                  </dt>
                  <dd className="mt-1 font-mono text-xs">{lastMessageRole}</dd>
                </div>
                <div>
                  <dt className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                    Total messages
                  </dt>
                  <dd className="mt-1 font-mono text-xs">{messageCount}</dd>
                </div>
              </dl>
            </CollapsibleSection>

            <CollapsibleSection title="Raw session snapshot">
              <RawJson
                value={{
                  sessionId,
                  persona,
                  recommendations,
                  messages: chatState.messages,
                }}
              />
            </CollapsibleSection>
          </>
        )}
      </div>
    </section>
  );
}

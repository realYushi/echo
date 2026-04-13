"use client";

import { useEffect, useState } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { RecommendationGrid } from "@/components/recommendations/RecommendationGrid";
import { Button } from "@/components/ui/Button";
import { useChat } from "@/hooks/useChat";
import { usePersona } from "@/hooks/usePersona";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useSessionId } from "@/hooks/useSessionId";
import { fetchSessionSnapshot } from "@/lib/api";
import type { Message } from "@/types/chat";
import { EMPTY_PERSONA } from "@/types/persona";

function createHydratedMessageId(index: number, role: Message["role"]): string {
  return `restored-${role}-${index}-${crypto.randomUUID()}`;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function getHydrationErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to restore your last discovery session right now.";
}

export default function DiscoverPage() {
  const { sessionId, isReady, startNewSession } = useSessionId();
  const [isHydrating, setIsHydrating] = useState(false);
  const [hydrationError, setHydrationError] = useState<string | null>(null);
  const resolvedSessionId = sessionId ?? "";

  const persona = usePersona(resolvedSessionId);
  const recommendations = useRecommendations(resolvedSessionId);
  const chat = useChat(resolvedSessionId, {
    persona: persona.persona,
    onPersonaUpdate: persona.setPersona,
    onTurnComplete: async () => {
      await recommendations.refreshRecommendations();
    },
  });
  const replaceMessages = chat.replaceMessages;
  const setPersona = persona.setPersona;
  const setRecommendations = recommendations.setRecommendations;

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const controller = new AbortController();
    setIsHydrating(true);
    setHydrationError(null);

    void fetchSessionSnapshot(sessionId, controller.signal)
      .then((snapshot) => {
        replaceMessages(
          snapshot.messages.map((message, index) => ({
            id: createHydratedMessageId(index, message.role),
            role: message.role,
            content: message.content,
          })),
        );
        setPersona(snapshot.persona ?? EMPTY_PERSONA);
        setRecommendations(snapshot.recommendations);
      })
      .catch((error: unknown) => {
        if (isAbortError(error)) {
          return;
        }

        replaceMessages([]);
        setPersona(EMPTY_PERSONA);
        setRecommendations([]);
        setHydrationError(getHydrationErrorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsHydrating(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [
    replaceMessages,
    setPersona,
    setRecommendations,
    sessionId,
  ]);

  const signalChips = [
    ...persona.persona.categories,
    ...persona.persona.stylePreferences,
    ...persona.persona.materialPreferences,
  ].slice(0, 6);
  const recentApprovals = persona.persona.approvals.slice(-2);
  const recentRejections = persona.persona.rejections.slice(-2);
  const hasConversation = chat.messages.length > 0;

  async function handleFeedback(productId: string, signal: "like" | "dislike") {
    const updatedPersona = await persona.sendFeedback(productId, signal);
    if (updatedPersona) {
      await recommendations.refreshRecommendations();
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(46,106,79,0.16),transparent_26%),radial-gradient(circle_at_bottom_right,rgba(125,84,48,0.12),transparent_22%),linear-gradient(180deg,#f7f1e8_0%,#efe5d6_100%)]">
      <div className="pointer-events-none absolute inset-0 opacity-70">
        <div className="absolute top-[-6rem] left-[-8rem] h-64 w-64 rounded-full bg-[color:var(--accent)]/12 blur-3xl" />
        <div className="absolute right-[-5rem] bottom-[-10rem] h-72 w-72 rounded-full bg-[#b9824a]/12 blur-3xl" />
      </div>
      <div className="relative mx-auto flex min-h-screen w-full max-w-[1600px] flex-col p-4 sm:p-6 xl:p-8">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-[28px] border border-[color:var(--line)] bg-white/60 px-5 py-4 shadow-[0_24px_50px_rgba(29,42,34,0.08)] backdrop-blur-sm">
          <div>
            <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
              Echo
            </p>
            <h1 className="mt-2 text-3xl text-[color:var(--ink)] sm:text-4xl">
              Discovery Studio
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs tracking-[0.16em] text-[color:var(--muted)] uppercase">
            <span className="rounded-full border border-[color:var(--line)] bg-white/80 px-3 py-2">
              Session {sessionId ? sessionId.slice(0, 8) : "loading"}
            </span>
            <span className="rounded-full border border-[color:var(--line)] bg-white/80 px-3 py-2">
              {recommendations.products.length} live picks
            </span>
            <Button
              variant="secondary"
              className="rounded-full border-[color:var(--line)] bg-white/80 px-3 py-2 text-[11px] tracking-[0.16em] uppercase"
              onClick={startNewSession}
            >
              New session
            </Button>
          </div>
        </div>

        <div className="grid flex-1 gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(340px,0.75fr)]">
          <section className="min-h-[40rem] overflow-hidden rounded-[32px] border border-[color:var(--line)] bg-[color:var(--panel)]/92 shadow-[0_28px_80px_rgba(29,42,34,0.1)] backdrop-blur-sm">
            <ChatPanel
              messages={chat.messages}
              onSend={chat.sendMessage}
              isStreaming={chat.isStreaming}
              inputDisabled={!isReady || isHydrating || chat.isStreaming}
              statusLabel={
                !isReady ? "Loading" : isHydrating ? "Restoring" : undefined
              }
              error={chat.error ?? hydrationError}
            />
          </section>

          <aside className="flex min-h-[40rem] flex-col gap-4">
            <section className="rounded-[32px] border border-[color:var(--line)] bg-white/70 p-5 shadow-[0_24px_60px_rgba(29,42,34,0.08)] backdrop-blur-sm">
              <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                Taste profile
              </p>
              <h2 className="mt-2 text-2xl text-[color:var(--ink)]">
                Signals coming into focus.
              </h2>
              <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
                Echo updates this profile as the conversation evolves, then uses
                it to reshape the shortlist in real time.
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                {signalChips.length > 0 ? (
                  signalChips.map((chip) => (
                    <span
                      key={chip}
                      className="rounded-full border border-[color:var(--line)] bg-[color:var(--accent-soft)]/55 px-3 py-1 text-xs text-[color:var(--ink)]"
                    >
                      {chip}
                    </span>
                  ))
                ) : (
                  <span className="rounded-full border border-dashed border-[color:var(--line)] px-3 py-1 text-xs text-[color:var(--muted)]">
                    Waiting for your first cues
                  </span>
                )}
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-[24px] border border-[color:var(--line)] bg-[color:var(--panel)] px-4 py-4">
                  <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                    Leaning toward
                  </p>
                  <div className="mt-3 space-y-2 text-sm text-[color:var(--ink)]">
                    {recentApprovals.length > 0 ? (
                      recentApprovals.map((item) => <p key={item}>{item}</p>)
                    ) : (
                      <p className="text-[color:var(--muted)]">
                        Positive reactions will show up here.
                      </p>
                    )}
                  </div>
                </div>
                <div className="rounded-[24px] border border-[color:var(--line)] bg-[color:var(--panel)] px-4 py-4">
                  <p className="text-[11px] tracking-[0.18em] text-[color:var(--muted)] uppercase">
                    Pull back from
                  </p>
                  <div className="mt-3 space-y-2 text-sm text-[color:var(--ink)]">
                    {recentRejections.length > 0 ? (
                      recentRejections.map((item) => <p key={item}>{item}</p>)
                    ) : (
                      <p className="text-[color:var(--muted)]">
                        Rejections help Echo learn even faster.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </section>

            <section className="flex-1 rounded-[32px] border border-[color:var(--line)] bg-white/70 p-5 shadow-[0_24px_60px_rgba(29,42,34,0.08)] backdrop-blur-sm">
              <RecommendationGrid
                products={recommendations.products}
                onFeedback={handleFeedback}
                isLoading={isHydrating || recommendations.isLoading}
                isFeedbackPending={persona.isSubmitting}
                error={persona.error ?? recommendations.error ?? hydrationError}
                emptyTitle={
                  hasConversation
                    ? "Keep shaping the direction"
                    : "Your shortlist will appear here"
                }
                emptyDescription={
                  hasConversation
                    ? "Add another preference, material, or rejection. Echo needs a bit more signal before the strongest matches rise to the top."
                    : "Start the conversation on the left and Echo will turn your reactions into a live set of product recommendations."
                }
              />
            </section>
          </aside>
        </div>
      </div>
    </main>
  );
}

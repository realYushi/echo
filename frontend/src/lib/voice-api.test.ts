import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchVoiceToken, postVoiceTranscript } from "@/lib/api";

describe("fetchVoiceToken", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns token and model on success", async () => {
    const responseData = {
      token: "auth_tokens/abc",
      model: "gemini-3.1-flash-live-preview",
    };

    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify(responseData), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await fetchVoiceToken();

    expect(result).toEqual({
      token: "auth_tokens/abc",
      model: "gemini-3.1-flash-live-preview",
    });
  });

  it("throws on non-ok response", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ error: { message: "Gemini API unavailable" } }),
        { status: 502 },
      ),
    );

    await expect(fetchVoiceToken()).rejects.toThrow("Gemini API unavailable");
  });
});

describe("postVoiceTranscript", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends correct payload and returns parsed response", async () => {
    const responseData = {
      sessionId: "session-v1",
      persona: {
        budgetTier: "premium",
        likes: ["warm oak"],
        hates: [],
        approvals: [],
        rejections: [],
      },
      recommendations: [
        {
          product: {
            id: "lighting-001",
            name: "Cascading Crystal Chandelier",
            category: "lighting",
            subcategory: "chandelier",
            tags: ["luxury", "crystal"],
            budgetTier: "premium",
            imageUrl: "https://example.com/light.png",
            description: "A dramatic lighting piece.",
          },
          score: 0.88,
        },
      ],
    };

    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify(responseData), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const messages = [
      { role: "user" as const, content: "I love warm oak tones" },
      { role: "assistant" as const, content: "Great taste! What about lighting?" },
    ];

    const result = await postVoiceTranscript("session-v1", messages);

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/voice/transcript",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ sessionId: "session-v1", messages }),
      }),
    );
    expect(result.sessionId).toBe("session-v1");
    expect(result.persona).toEqual(responseData.persona);
    expect(result.recommendations).toHaveLength(1);
    expect(result.recommendations[0].product.id).toBe("lighting-001");
  });

  it("throws on non-ok response", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ error: { message: "Internal server error" } }),
        { status: 500 },
      ),
    );

    await expect(
      postVoiceTranscript("session-v1", [
        { role: "user", content: "hello" },
      ]),
    ).rejects.toThrow("Internal server error");
  });
});

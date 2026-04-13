import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchRecommendations } from "@/lib/api";

describe("fetchRecommendations", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts only the session ID when using session-backed recommendations", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            product: {
              id: "lighting-001",
              name: "Cascading Crystal Chandelier",
              category: "lighting",
              subcategory: "chandelier",
              tags: ["luxury", "crystal", "lighting"],
              budgetTier: "premium",
              imageUrl: "https://example.com/light.png",
              description: "A dramatic lighting piece.",
            },
            score: 0.88,
          },
        ]),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    const recommendations = await fetchRecommendations("session-pr5");

    expect(recommendations).toHaveLength(1);
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/recommend",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ sessionId: "session-pr5" }),
      }),
    );
  });
});

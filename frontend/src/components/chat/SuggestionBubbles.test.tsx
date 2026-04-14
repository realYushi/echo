import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SuggestionBubbles } from "@/components/chat/SuggestionBubbles";

describe("SuggestionBubbles", () => {
  it("sends the selected suggestion through the shared send path", () => {
    const onSelect = vi.fn();

    render(
      <SuggestionBubbles
        suggestions={["Warm and natural", "Open to premium"]}
        onSelect={onSelect}
        disabled={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Warm and natural" }));

    expect(onSelect).toHaveBeenCalledWith("Warm and natural");
  });
});

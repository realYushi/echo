import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatInput } from "@/components/chat/ChatInput";

describe("ChatInput", () => {
  it("submits trimmed input and restores focus when re-enabled", () => {
    const onSend = vi.fn();
    const { rerender } = render(<ChatInput onSend={onSend} disabled={false} />);

    const input = screen.getByLabelText("Describe what you want to discover");
    expect(document.activeElement).toBe(input);

    fireEvent.change(input, { target: { value: "  Warm oak and stone  " } });
    fireEvent.submit(input.closest("form")!);

    expect(onSend).toHaveBeenCalledWith("Warm oak and stone");

    rerender(<ChatInput onSend={onSend} disabled={true} />);
    rerender(<ChatInput onSend={onSend} disabled={false} />);

    expect(document.activeElement).toBe(screen.getByLabelText("Describe what you want to discover"));
  });
});

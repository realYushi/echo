import { render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { ChatPanel } from "@/components/chat/ChatPanel";
import type { Message } from "@/types/chat";

beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

const defaultProps = {
  messages: [] as Message[],
  suggestions: [],
  onSend: vi.fn(),
  onSuggestionSelect: vi.fn(),
  isStreaming: false,
  error: null,
};

describe("ChatPanel", () => {
  it("renders text mode by default", () => {
    const messages: Message[] = [
      { id: "1", role: "user", content: "I want warm oak tones" },
      { id: "2", role: "assistant", content: "Great choice! Tell me more." },
    ];

    render(<ChatPanel {...defaultProps} messages={messages} />);

    expect(screen.getByText("I want warm oak tones")).toBeTruthy();
    expect(screen.getByText("Great choice! Tell me more.")).toBeTruthy();
    expect(
      screen.getByLabelText("Describe what you want to discover"),
    ).toBeTruthy();
  });

  it("renders voice slot when mode is voice", () => {
    render(
      <ChatPanel
        {...defaultProps}
        mode="voice"
        voiceSlot={<div data-testid="voice-slot" />}
      />,
    );

    expect(screen.getByTestId("voice-slot")).toBeTruthy();
    expect(
      screen.queryByLabelText("Describe what you want to discover"),
    ).toBeNull();
  });

  it("renders voice empty state when voice mode and no messages", () => {
    render(
      <ChatPanel
        {...defaultProps}
        mode="voice"
        voiceSlot={<div data-testid="voice-slot" />}
      />,
    );

    expect(screen.getByText("Voice discovery")).toBeTruthy();
  });

  it("renders text empty state when text mode and no messages", () => {
    render(<ChatPanel {...defaultProps} />);

    expect(screen.getByText("Try prompts like")).toBeTruthy();
  });

  it("shows Voice status badge in voice mode", () => {
    render(
      <ChatPanel
        {...defaultProps}
        mode="voice"
        voiceSlot={<div data-testid="voice-slot" />}
      />,
    );

    expect(screen.getByText("Voice")).toBeTruthy();
  });
});

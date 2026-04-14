import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { VoiceControls } from "@/components/chat/VoiceControls";

describe("VoiceControls", () => {
  it("renders idle state when not connected and not connecting", () => {
    render(
      <VoiceControls
        isConnected={false}
        isConnecting={false}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
      />,
    );

    const button = screen.getByRole("button");
    expect((button as HTMLButtonElement).disabled).toBe(false);
    expect(screen.getByText("Tap to start voice chat")).toBeTruthy();
  });

  it("renders connecting state", () => {
    render(
      <VoiceControls
        isConnected={false}
        isConnecting={true}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
      />,
    );

    const button = screen.getByRole("button");
    expect((button as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText("Connecting...")).toBeTruthy();
  });

  it("renders connected state", () => {
    render(
      <VoiceControls
        isConnected={true}
        isConnecting={false}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
      />,
    );

    const button = screen.getByRole("button");
    expect((button as HTMLButtonElement).disabled).toBe(false);
    expect(screen.getByText(/Listening/)).toBeTruthy();
  });

  it("calls onConnect when idle button is clicked", () => {
    const onConnect = vi.fn();
    render(
      <VoiceControls
        isConnected={false}
        isConnecting={false}
        onConnect={onConnect}
        onDisconnect={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button"));

    expect(onConnect).toHaveBeenCalledOnce();
  });

  it("calls onDisconnect when connected button is clicked", () => {
    const onDisconnect = vi.fn();
    render(
      <VoiceControls
        isConnected={true}
        isConnecting={false}
        onConnect={vi.fn()}
        onDisconnect={onDisconnect}
      />,
    );

    fireEvent.click(screen.getByRole("button"));

    expect(onDisconnect).toHaveBeenCalledOnce();
  });

  it("does not call handlers when connecting", () => {
    const onConnect = vi.fn();
    const onDisconnect = vi.fn();
    render(
      <VoiceControls
        isConnected={false}
        isConnecting={true}
        onConnect={onConnect}
        onDisconnect={onDisconnect}
      />,
    );

    fireEvent.click(screen.getByRole("button"));

    expect(onConnect).not.toHaveBeenCalled();
    expect(onDisconnect).not.toHaveBeenCalled();
  });
});

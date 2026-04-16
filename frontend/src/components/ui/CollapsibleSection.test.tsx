import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CollapsibleSection } from "@/components/ui/CollapsibleSection";

describe("CollapsibleSection", () => {
  it("starts collapsed by default and expands on click", () => {
    render(
      <CollapsibleSection title="Details">
        <p>Body content</p>
      </CollapsibleSection>,
    );

    const toggle = screen.getByRole("button", { name: /Details/i });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");

    const bodyId = toggle.getAttribute("aria-controls");
    expect(bodyId).toBeTruthy();
    if (!bodyId) {
      throw new Error("aria-controls not set");
    }
    expect(document.getElementById(bodyId)?.hasAttribute("hidden")).toBe(true);

    fireEvent.click(toggle);

    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(document.getElementById(bodyId)?.hasAttribute("hidden")).toBe(false);
    expect(screen.getByText("Body content")).toBeTruthy();
  });

  it("collapses again after a second click when defaultOpen is true", () => {
    render(
      <CollapsibleSection title="Details" defaultOpen>
        <p>Body content</p>
      </CollapsibleSection>,
    );

    const toggle = screen.getByRole("button", { name: /Details/i });
    expect(toggle.getAttribute("aria-expanded")).toBe("true");

    fireEvent.click(toggle);

    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    const bodyId = toggle.getAttribute("aria-controls");
    if (!bodyId) {
      throw new Error("aria-controls not set");
    }
    expect(document.getElementById(bodyId)?.hasAttribute("hidden")).toBe(true);
  });

  it("honours defaultOpen=true on first render", () => {
    render(
      <CollapsibleSection title="Details" defaultOpen>
        <p>Body content</p>
      </CollapsibleSection>,
    );

    const toggle = screen.getByRole("button", { name: /Details/i });
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText("Body content")).toBeTruthy();
  });
});

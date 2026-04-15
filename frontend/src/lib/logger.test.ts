import { describe, expect, it } from "vitest";
import { createLogger, getRequestId, setRequestId } from "@/lib/logger";

describe("logger", () => {
  it("creates a child logger with the given module name", () => {
    const log = createLogger("test-module");
    expect(log.bindings().module).toBe("test-module");
  });

  it("generates a request ID when none is set", () => {
    const id = getRequestId();
    expect(id).toHaveLength(12);
  });

  it("returns the same request ID once generated", () => {
    const first = getRequestId();
    const second = getRequestId();
    expect(first).toBe(second);
  });

  it("uses the request ID set via setRequestId", () => {
    setRequestId("custom-id-123");
    expect(getRequestId()).toBe("custom-id-123");
    // Reset for other tests
    setRequestId("");
  });
});

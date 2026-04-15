import pino from "pino";

let requestId = "";

export function setRequestId(id: string): void {
  requestId = id;
}

export function getRequestId(): string {
  if (!requestId) {
    requestId = crypto.randomUUID().slice(0, 12);
  }
  return requestId;
}

function createRootLogger(): pino.Logger {
  if (typeof window === "undefined") {
    return pino({ level: "silent" });
  }

  return pino({
    level: process.env.NODE_ENV === "production" ? "warn" : "debug",
    browser: {
      asObject: true,
    },
  });
}

const root = createRootLogger();

export function createLogger(module: string): pino.Logger {
  return root.child({ module });
}

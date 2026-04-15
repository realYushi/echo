"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { createLogger } from "@/lib/logger";

const logger = createLogger("ErrorBoundary");

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    logger.error(
      { err: error, componentStack: errorInfo.componentStack, event: "react_render_error" },
      "Uncaught rendering error",
    );
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-[color:var(--surface)]">
          <div className="max-w-md rounded-2xl border border-[color:var(--line)] bg-white/80 p-8 text-center shadow-lg">
            <h2 className="text-xl text-[color:var(--ink)]">Something went wrong</h2>
            <p className="mt-3 text-sm text-[color:var(--muted)]">
              Echo hit an unexpected error. This has been logged for investigation.
            </p>
            <button
              type="button"
              onClick={() => this.setState({ hasError: false, message: "" })}
              className="mt-5 rounded-xl bg-[color:var(--ink)] px-4 py-2 text-sm text-white transition hover:opacity-90"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "../test-utils";
import { ErrorBoundary } from "../../components/layout/ErrorBoundary";
import * as Sentry from "@sentry/react";

vi.mock("@sentry/react", () => ({
  captureException: vi.fn(),
}));

function Bomb() {
  throw new Error("💥");
  return null;
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <div>Safe</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Safe")).toBeInTheDocument();
  });

  it("catches errors and shows fallback", () => {
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Try Again")).toBeInTheDocument();
  });

  it("reports the error to Sentry", () => {
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    );
    expect(Sentry.captureException).toHaveBeenCalledTimes(1);
    const [error, context] = vi.mocked(Sentry.captureException).mock.calls[0];
    expect((error as Error).message).toBe("💥");
    expect(context).toMatchObject({ extra: { componentStack: expect.any(String) } });
  });
});

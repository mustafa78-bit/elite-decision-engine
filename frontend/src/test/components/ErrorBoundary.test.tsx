import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { ErrorBoundary } from "../../components/layout/ErrorBoundary";

function Bomb(): any {
  throw new Error("💥");
}

describe("ErrorBoundary", () => {
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
});

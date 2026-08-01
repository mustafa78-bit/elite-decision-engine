import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "../test-utils";
import { ErrorRetry } from "../../components/ui/ErrorRetry";

describe("ErrorRetry", () => {
  it("renders message and retry button", () => {
    const retry = vi.fn();
    render(<ErrorRetry message="Failed to load" onRetry={retry} />);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("calls onRetry when clicked", () => {
    const retry = vi.fn();
    render(<ErrorRetry onRetry={retry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(retry).toHaveBeenCalledOnce();
  });
});

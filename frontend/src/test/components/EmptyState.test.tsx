import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { EmptyState } from "../../components/ui/EmptyState";

describe("EmptyState", () => {
  it("renders default message", () => {
    render(<EmptyState />);
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<EmptyState message="No trades found" />);
    expect(screen.getByText("No trades found")).toBeInTheDocument();
  });
});

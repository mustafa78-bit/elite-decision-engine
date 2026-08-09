import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { ConnectionIndicator } from "../../components/layout/connection-indicator";

describe("ConnectionIndicator", () => {
  it("renders connected state", () => {
    render(<ConnectionIndicator status="connected" />);
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("renders disconnected state", () => {
    render(<ConnectionIndicator status="disconnected" />);
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });

  it("renders reconnecting state", () => {
    render(<ConnectionIndicator status="reconnecting" />);
    expect(screen.getByText("Reconnecting...")).toBeInTheDocument();
  });

  it("renders custom label", () => {
    render(<ConnectionIndicator status="connected" label="Custom" />);
    expect(screen.getByText("Custom")).toBeInTheDocument();
  });
});

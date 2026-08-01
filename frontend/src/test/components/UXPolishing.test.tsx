import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { ConnectionIndicator } from "../../components/layout/connection-indicator";
import { ChartToolbar } from "../../components/trading/chart-toolbar";
import { ChartMarkers } from "../../components/trading/chart-markers";
import { ChartOverlays } from "../../components/trading/chart-overlays";

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

describe("ChartToolbar", () => {
  it("renders toolbar buttons", () => {
    render(<ChartToolbar />);
    expect(screen.getByText("Draw")).toBeInTheDocument();
    expect(screen.getByText("Marker")).toBeInTheDocument();
    expect(screen.getByText("Crosshair")).toBeInTheDocument();
    expect(screen.getByText("Reset")).toBeInTheDocument();
  });

  it("shows active state for drawing mode", () => {
    render(<ChartToolbar drawingMode />);
    expect(screen.getByText("Draw").closest("button")).toHaveClass("bg-[var(--accent-blue)]/15");
  });
});

describe("ChartMarkers", () => {
  it("shows empty state", () => {
    render(<ChartMarkers />);
    expect(screen.getByText("No markers on chart")).toBeInTheDocument();
  });

  it("renders markers", () => {
    const markers = [
      { id: "m1", type: "enter" as const, symbol: "BTC/USDT", price: 42100, time: "10:30", label: "Long Entry", direction: "long" as const },
    ];
    render(<ChartMarkers markers={markers} />);
    expect(screen.getByText("Long Entry")).toBeInTheDocument();
    expect(screen.getByText("@ 42100")).toBeInTheDocument();
  });
});

describe("ChartOverlays", () => {
  it("renders overlay button", () => {
    render(<ChartOverlays />);
    expect(screen.getByText(/Overlays/)).toBeInTheDocument();
  });
});

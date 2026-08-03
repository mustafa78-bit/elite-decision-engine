import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "../test-utils";
import ScannerOpportunitiesPanel from "../../components/dashboard/ScannerOpportunitiesPanel";
import type { ScannerDashboard } from "../../api/scanner";

const { fetchScannerDashboard } = vi.hoisted(() => ({
  fetchScannerDashboard: vi.fn(),
}));

vi.mock("../../api/scanner", async () => {
  const actual = await vi.importActual<typeof import("../../api/scanner")>("../../api/scanner");
  return { ...actual, fetchScannerDashboard };
});

function makeDashboard(overrides: Partial<ScannerDashboard> = {}): ScannerDashboard {
  return {
    symbols_scanned: 25,
    opportunities_found: 2,
    top_opportunities: [
      {
        rank: 1,
        symbol: "BTCUSDT",
        side: "LONG",
        strategy: "trend",
        score: 0.82,
        probability: 0.7,
        risk_score: 0.2,
        confidence: 0.85,
        price: 63000,
        signals: ["BULLISH_TREND_ALIGNED", "HIGH_VOLUME_CONFIRMATION"],
      },
      {
        rank: 2,
        symbol: "ETHUSDT",
        side: "SHORT",
        strategy: "reversal",
        score: 0.65,
        probability: 0.6,
        risk_score: 0.3,
        confidence: 0.6,
        price: 3400,
        signals: ["OVERBOUGHT_REVERSAL"],
      },
    ],
    top_signals: [],
    market_summary: {},
    intelligence_summary: {},
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe("ScannerOpportunitiesPanel", () => {
  beforeEach(() => {
    fetchScannerDashboard.mockReset();
  });

  it("shows a loading skeleton", () => {
    fetchScannerDashboard.mockReturnValue(new Promise(() => {}));
    render(<ScannerOpportunitiesPanel />);
    expect(screen.getByText("Ranked Opportunities")).toBeInTheDocument();
  });

  it("shows an error state with a retry button", async () => {
    fetchScannerDashboard.mockRejectedValue(new Error("network down"));
    render(<ScannerOpportunitiesPanel />);
    await waitFor(() => expect(screen.getByText("Failed to load")).toBeInTheDocument());

    fetchScannerDashboard.mockResolvedValueOnce(makeDashboard());
    fireEvent.click(screen.getByText("Retry"));
    await waitFor(() => expect(screen.getByText("BTCUSDT")).toBeInTheDocument());
  });

  it("shows an empty state when there are no opportunities", async () => {
    fetchScannerDashboard.mockResolvedValue(makeDashboard({ top_opportunities: [], opportunities_found: 0 }));
    render(<ScannerOpportunitiesPanel />);
    await waitFor(() => expect(screen.getByText("No opportunities found")).toBeInTheDocument());
  });

  it("renders both LONG and SHORT opportunities with distinct visual treatment", async () => {
    fetchScannerDashboard.mockResolvedValue(makeDashboard());
    render(<ScannerOpportunitiesPanel />);

    await waitFor(() => expect(screen.getByText("BTCUSDT")).toBeInTheDocument());
    expect(screen.getByText("ETHUSDT")).toBeInTheDocument();
    expect(screen.getByText("▲")).toBeInTheDocument();
    expect(screen.getByText("▼")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("60%")).toBeInTheDocument();
    expect(screen.getByText("2 found")).toBeInTheDocument();
  });
});

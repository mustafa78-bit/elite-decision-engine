// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "../test-utils";
import Dashboard from "../../pages/Dashboard";

// Mock the react-router-dom's useOutletContext
const mockContext = {
  notifications: [
    {
      event: "TRADE_OPENED" as const,
      timestamp: new Date().toISOString(),
      payload: { symbol: "BTC", side: "LONG", entry: 64000, status: "OPEN" },
    },
  ],
  openTrades: [
    { symbol: "BTC", side: "LONG", entry: 64000, status: "OPEN", pnl: 250.75 },
  ],
  closedTrades: [
    { symbol: "ETH", side: "SHORT", entry: 3500, exit_price: 3450, status: "CLOSED", pnl: 150 },
  ],
  latestIntelligence: {
    confidence: 0.85,
    decision: "STRONG BUY",
    final_score: 0.88,
    trend_score: 0.9,
    volume_score: 0.8,
    btc_score: 0.85,
    mtf_score: 0.75,
    risk_score: 0.4,
    rsi: 58,
    ema20: 63000,
    ema50: 62000,
    ema200: 60000,
  },
  latestPrice: {
    symbol: "BTC",
    price: 64500,
    change_24h: 1.84,
    volume: 1200000000,
  },
};

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useOutletContext: () => mockContext,
  };
});

describe("Dashboard Terminal Page", () => {
  beforeEach(() => {
    // Reset mockContext state
    mockContext.openTrades = [
      { symbol: "BTC", side: "LONG", entry: 64000, status: "OPEN", pnl: 250.75 },
    ];
  });

  it("renders premium Bloomberg-style trading terminal metrics", () => {
    render(<Dashboard />);

    // Header title
    expect(screen.getByText("ELITE DECISION INTELLIGENCE TERMINAL")).toBeInTheDocument();

    // Decision intelligence metrics
    expect(screen.getByText("// DECISION INTELLIGENCE CONSOLE")).toBeInTheDocument();
    expect(screen.getByText("STRONG BUY")).toBeInTheDocument();
    expect(screen.getByText("88/100")).toBeInTheDocument();

    // Market intelligence metrics
    expect(screen.getByText("// GLOBAL MARKET INTELLIGENCE")).toBeInTheDocument();
    expect(screen.getByText("BTC dominance: 54.2%")).toBeInTheDocument();

    // Risk assessment metrics
    expect(screen.getByText("// RISK ASSESSMENT CENTRE")).toBeInTheDocument();
    expect(screen.getByText("MEDIUM RISK")).toBeInTheDocument();

    // Watchlists & sector views
    expect(screen.getByText("// SECTOR WATCHLISTS")).toBeInTheDocument();
    expect(screen.getByText("BTC/USDT")).toBeInTheDocument();
  });

  it("supports switching tabs inside execution ledger", async () => {
    render(<Dashboard />);

    // Locate tab buttons inside Execution Ledger
    const activeTabBtn = screen.getByRole("button", { name: "active" });
    const closedTabBtn = screen.getByRole("button", { name: "closed" });

    // Click 'closed' trades tab
    fireEvent.click(closedTabBtn);

    // Use findByText to await async rendering/animations of the tab panels
    const realizedPnlElement = await screen.findByText("REALIZED PNL");
    expect(realizedPnlElement).toBeInTheDocument();

    // Switch back to 'active' trades tab
    fireEvent.click(activeTabBtn);
    const unrealizedPnlElement = await screen.findByText("UNREALIZED PNL");
    expect(unrealizedPnlElement).toBeInTheDocument();
    expect(screen.getAllByText("BTC").length).toBeGreaterThan(0);
  });

  it("handles empty states correctly", () => {
    mockContext.openTrades = [];
    render(<Dashboard />);
    expect(screen.getByText("No active leveraged trades in execution.")).toBeInTheDocument();
  });
});

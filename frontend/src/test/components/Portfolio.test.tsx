import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "../test-utils";
import Portfolio from "../../pages/Portfolio";

// Mock react-router-dom for useOutletContext and useNavigate
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useOutletContext: () => ({
      openTrades: [
        { symbol: "BTCUSDT", side: "LONG", entry: 50000.0, status: "OPEN", pnl: 150.0 },
      ],
    }),
  };
});

describe("Portfolio Command Center", () => {
  beforeEach(() => {
    // Stub the global fetch API to return our mocked PortfolioFullDTO payload
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        summary: {
          total_balance: 10500.0,
          open_pnl: 150.0,
          realized_pnl: 350.0,
          total_pnl: 500.0,
          total_trades: 12,
          open_trades: 2,
          win_rate: 66.7,
          profit_factor: 2.1,
          sharpe_ratio: 1.65,
          max_drawdown: 4.5,
          current_drawdown: 1.2,
          avg_trade_duration: "4h 12m",
          best_trade_pnl: 150.0,
          worst_trade_pnl: -40.0,
          health_score: 92.5,
          volatility: 12.4,
        },
        distribution: {
          by_symbol: [
            { symbol: "BTCUSDT", trades: 8, wins: 5, pnl: 450.0, win_rate: 62.5 },
            { symbol: "ETHUSDT", trades: 4, wins: 3, pnl: 50.0, win_rate: 75.0 },
          ],
          by_side: { LONG: 9, SHORT: 3 },
        },
        performance: {
          equity_curve: [
            { timestamp: "2026-07-01T00:00:00Z", equity: 10000.0 },
            { timestamp: "2026-07-02T00:00:00Z", equity: 10150.0 },
            { timestamp: "2026-07-03T00:00:00Z", equity: 10500.0 },
          ],
          monthly_pnl: [{ month: "2026-07", pnl: 500.0 }],
          daily_pnl: [
            { date: "2026-07-01", pnl: 0.0 },
            { date: "2026-07-02", pnl: 150.0 },
            { date: "2026-07-03", pnl: 350.0 },
          ],
          drawdown_curve: [
            { timestamp: "2026-07-01T00:00:00Z", drawdown: 0.0 },
            { timestamp: "2026-07-02T00:00:00Z", drawdown: 1.2 },
          ],
        },
        risk: {
          current_exposure: 5000.0,
          max_exposure: 15000.0,
          symbol_concentration: { BTCUSDT: 0.7, ETHUSDT: 0.3 },
          risk_per_trade: 250.0,
          var_95: 120.0,
          expected_downside: 45.0,
          recovery_factor: 2.8,
          diversification: {
            hhi: 0.58,
            shannon_entropy: 0.61,
            diversification_status: "MODERATELY_DIVERSIFIED",
            diversification_score: 72.0,
          },
          correlation_matrix: {
            BTCUSDT: { BTCUSDT: 1.0, ETHUSDT: 0.85 },
            ETHUSDT: { BTCUSDT: 0.85, ETHUSDT: 1.0 },
          },
          ai_insights: [
            {
              type: "HEALTH",
              level: "INFO",
              title: "Excellent Sharpe Ratio",
              message: "Your portfolio exhibits a strong risk-adjusted return profile.",
              recommendation: "Maintain current risk parameters.",
            },
          ],
        },
      }),
    }));
  });

  it("renders layout, title, and initial Overview tab correctly", async () => {
    render(<Portfolio />);

    // Wait for the full command center layout to load from fetch
    await waitFor(() => {
      expect(screen.getByText(/Portfolio Intelligence & Risk Command Center/i)).toBeInTheDocument();
    });

    // Check key overview stats
    expect(screen.getByText("92.5%")).toBeInTheDocument(); // Health Index Score
    expect(screen.getByText("66.7%")).toBeInTheDocument(); // Win rate
    expect(screen.getByText("1.65")).toBeInTheDocument(); // Sharpe Ratio
    expect(screen.getByText("4.5%")).toBeInTheDocument(); // Max DD
  });

  it("can switch to Allocation tab", async () => {
    render(<Portfolio />);

    await waitFor(() => {
      expect(screen.getByText(/Portfolio Intelligence & Risk Command Center/i)).toBeInTheDocument();
    });

    const allocTabButton = screen.getByRole("button", { name: /Allocation/i });
    fireEvent.click(allocTabButton);

    expect(screen.getByText("Asset Allocation Weightings")).toBeInTheDocument();
    expect(screen.getByText("70.0% Weight")).toBeInTheDocument(); // Concentration for BTCUSDT
    expect(screen.getByText("30.0% Weight")).toBeInTheDocument(); // Concentration for ETHUSDT
  });

  it("can switch to Correlation Heatmap tab", async () => {
    render(<Portfolio />);

    await waitFor(() => {
      expect(screen.getByText(/Portfolio Intelligence & Risk Command Center/i)).toBeInTheDocument();
    });

    const correlationTabButton = screen.getByRole("button", { name: /Correlation Heatmap/i });
    fireEvent.click(correlationTabButton);

    expect(screen.getByText("Pairwise Asset Correlation Heatmap")).toBeInTheDocument();
    expect(screen.getAllByText("0.85").length).toBeGreaterThan(0); // correlation coefficient matches
  });

  it("can switch to AI Insights tab", async () => {
    render(<Portfolio />);

    await waitFor(() => {
      expect(screen.getByText(/Portfolio Intelligence & Risk Command Center/i)).toBeInTheDocument();
    });

    const insightsTabButton = screen.getByRole("button", { name: /AI Insights/i });
    fireEvent.click(insightsTabButton);

    expect(screen.getByText("Excellent Sharpe Ratio")).toBeInTheDocument();
    expect(screen.getByText("Your portfolio exhibits a strong risk-adjusted return profile.")).toBeInTheDocument();
  });
});

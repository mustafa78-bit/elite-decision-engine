import { beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "../test-utils";
import Backtest from "../../pages/Backtest";

// Mock global API fetch methods
const mockTemplates = [
  {
    id: "template_trend_following",
    name: "Trend Following (EMA + Whale flow)",
    description: "Enters LONG when medium-term trend is bullish.",
    rules: [
      { type: "indicator", param: "trend_score", operator: ">=", value: 0.7 },
    ],
    parameters: { stop_loss_pct: 2.0, take_profit_pct: 5.0, risk_pct: 1.5 },
  },
];

const mockSaved = [
  {
    id: 42,
    name: "Saved Strategy Alpha",
    description: "Saved description",
    rules: [
      { type: "whale", param: "cvd_score", operator: ">=", value: 0.8 },
    ],
    parameters: { stop_loss_pct: 1.0, take_profit_pct: 3.0, risk_pct: 1.0 },
  },
];

const mockBacktestResult = {
  summary: {
    total_signals_scanned: 100,
    signals_filtered: 15,
    capital_utilized: 10000.0,
  },
  performance: {
    total_pnl: 1450.0,
    roi_pct: 14.5,
    win_rate_pct: 60.0,
    win_rate_long_pct: 65.0,
    win_rate_short_pct: 50.0,
    avg_win: 250.0,
    avg_loss: 100.0,
    profit_factor: 2.5,
    max_drawdown: 350.0,
    max_drawdown_pct: 3.5,
    sharpe_ratio: 1.62,
    sortino_ratio: 1.85,
    calmar_ratio: 4.14,
    expectancy: 110.0,
  },
  trades: [
    {
      id: 1,
      symbol: "BTC",
      side: "LONG",
      entry: 60000.0,
      exit: 63000.0,
      quantity: 0.1,
      pnl: 300.0,
      status: "CLOSED",
      close_reason: "TP_HIT",
      created_at: "2025-01-01T12:00:00Z",
      closed_at: "2025-01-02T12:00:00Z",
    },
  ],
  equity_curve: [{ timestamp: "2025-01-01T12:00:00Z", equity: 10300.0 }],
  monthly_pnl: { "2025-01": 300.0 },
};

describe("StrategyLab (Backtest Workspace)", () => {
  beforeAll(() => {
    // Setup fetch mock globally for vitest
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/strategy-lab/templates")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTemplates),
          });
        }
        if (url.includes("/strategy-lab/saved")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSaved),
          });
        }
        if (url.includes("/strategy-lab/backtest")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockBacktestResult),
          });
        }
        if (url.includes("/strategy-lab/optimize")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              best_parameters: { stop_loss_pct: 2.0, take_profit_pct: 5.0, risk_pct: 1.5 },
              best_sharpe: 1.62,
              trials: []
            }),
          });
        }
        if (url.includes("/strategy-lab/walk-forward")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              windows: [],
              avg_train_sharpe: 1.2,
              avg_test_sharpe: 1.1,
              stability: 0.9,
              combined_test_pnl: 1000.0
            }),
          });
        }
        if (url.includes("/strategy-lab/monte-carlo")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              simulations: [],
              metrics: {
                probability_of_ruin_pct: 0.0,
                avg_drawdown_pct: 5.0,
                percentile_95_drawdown_pct: 8.0,
                median_terminal_equity: 12000.0,
                min_terminal_equity: 10500.0,
                max_terminal_equity: 15000.0
              }
            }),
          });
        }
        if (url.includes("/strategy-lab/ai-analyze")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                strengths: ["Strong Sharpe ratio"],
                weaknesses: ["None"],
                improvements: ["Add Trailing SL"],
                missing_filters: ["BTC health filter"],
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        });
      })
    );
  });

  it("renders continuous workspace title and header elements", async () => {
    render(<Backtest />);
    expect(screen.getByText("Institutional Strategy Lab")).toBeInTheDocument();
    expect(screen.getByText("Research, Backtest, Optimize & Validate System Rules")).toBeInTheDocument();
    expect(screen.getByText("Save Strategy")).toBeInTheDocument();
  });

  it("loads templates and saved strategies into the repository display", async () => {
    render(<Backtest />);
    await waitFor(() => {
      expect(screen.getByText("Trend Following (EMA + Whale flow)")).toBeInTheDocument();
    });
  });

  it("allows adding and updating rules inside the visual builder", async () => {
    render(<Backtest />);
    const addBtn = screen.getByText("+ Add Condition");
    fireEvent.click(addBtn);

    // Verify a new rule dropdown is present
    await waitFor(() => {
      const dropdowns = screen.getAllByRole("combobox");
      expect(dropdowns.length).toBeGreaterThan(0);
    });
  });

  it("can switch between backtest, optimizer, walkforward, and montecarlo tabs", async () => {
    render(<Backtest />);

    // Tab 1: Optimizer
    const optimizeTab = screen.getByText("◈ Optimizer");
    fireEvent.click(optimizeTab);
    await waitFor(() => {
      expect(screen.getByText("Parameter Grid Optimizer")).toBeInTheDocument();
    });

    // Tab 2: Walk Forward
    const walkforwardTab = screen.getByText("⇄ Walk Forward");
    fireEvent.click(walkforwardTab);
    await waitFor(() => {
      expect(screen.getByText("Walk Forward Robustness Analysis")).toBeInTheDocument();
    });

    // Tab 3: Monte Carlo
    const montecarloTab = screen.getByText("✦ Monte Carlo");
    fireEvent.click(montecarloTab);
    await waitFor(() => {
      expect(screen.getByText("Monte Carlo Probability Simulation")).toBeInTheDocument();
    });
  });
});

import { apiFetch } from "./client";

export interface BacktestResult {
  summary: {
    total_signals: number;
    approved_signals: number;
    rejected_signals: number;
    approval_rate: number;
  };
  trades: {
    total: number;
    open: number;
    closed: number;
    wins: number;
    losses: number;
  };
  performance: {
    total_pnl: number;
    roi_pct: number;
    win_rate_pct: number;
    avg_win: number;
    avg_loss: number;
    profit_factor: number;
    max_drawdown: number;
    sharpe_ratio: number;
  };
}

export function fetchBacktest(limit = 200): Promise<BacktestResult> {
  return apiFetch<BacktestResult>(`/backtest?limit=${limit}`);
}

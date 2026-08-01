import { apiFetch } from "./client";

export interface PortfolioStats {
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  loss_rate: number;
  total_pnl: number;
  daily_pnl: number;
  average_win: number;
  average_loss: number;
  average_pnl: number;
  profit_factor: number;
  max_drawdown: number;
  current_open_exposure: number;
  equity_curve: number[];
  equity: number;
  allocation: Record<string, number>;
  unrealized_pnl: number;
}

export function fetchPortfolio(): Promise<PortfolioStats> {
  return apiFetch<PortfolioStats>("/portfolio");
}

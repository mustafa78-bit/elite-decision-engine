export interface PortfolioSummaryDTO {
  total_pnl: number;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  profit_factor: number;
  sharpe: number;
  max_drawdown: number;
  calmar: number;
  open_pnl: number;
  open_trades: number;
}

export interface PortfolioDistributionDTO {
  by_symbol: Record<string, number>;
  by_side: Record<string, number>;
  by_status: Record<string, number>;
}

export interface PortfolioPerformanceDTO {
  equity_curve: { time: string; value: number }[];
  monthly_returns: Record<string, number>;
  best_trade: number;
  worst_trade: number;
  avg_win: number;
  avg_loss: number;
}

export interface PortfolioRiskDTO {
  value_at_risk: number;
  sharpe: number;
  sortino: number;
  calmar: number;
  max_drawdown: number;
  recovery_factor: number;
}

export interface PortfolioFullDTO {
  summary: PortfolioSummaryDTO;
  distribution: PortfolioDistributionDTO;
  performance: PortfolioPerformanceDTO;
  risk: PortfolioRiskDTO;
}

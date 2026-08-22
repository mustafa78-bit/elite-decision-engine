// Matches services/portfolio_service.py's PortfolioService.full_portfolio()
// response shape exactly (backing GET /portfolio/full).
export interface PortfolioSummaryDTO {
  total_balance: number;
  open_pnl: number;
  realized_pnl: number;
  total_pnl: number;
  total_trades: number;
  open_trades: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  current_drawdown: number;
  avg_trade_duration: string | null;
  best_trade_pnl: number;
  worst_trade_pnl: number;
}

export interface PortfolioDistributionBySymbol {
  symbol: string;
  trades: number;
  wins: number;
  pnl: number;
  win_rate: number;
}

export interface PortfolioDistributionDTO {
  by_symbol: PortfolioDistributionBySymbol[];
  by_side: { LONG: number; SHORT: number };
}

export interface PortfolioPerformanceDTO {
  equity_curve: { timestamp: string | null; value: number }[];
  monthly_pnl: { month: string; pnl: number }[];
  daily_pnl: { date: string; pnl: number }[];
  drawdown_curve: { timestamp: string | null; drawdown: number }[];
}

export interface PortfolioRiskDTO {
  current_exposure: number;
  max_exposure: number;
  symbol_concentration: Record<string, number>;
  risk_per_trade: number;
  var_95: number;
  expected_downside: number;
  recovery_factor: number;
}

export interface PortfolioFullDTO {
  summary: PortfolioSummaryDTO;
  distribution: PortfolioDistributionDTO;
  performance: PortfolioPerformanceDTO;
  risk: PortfolioRiskDTO;
}

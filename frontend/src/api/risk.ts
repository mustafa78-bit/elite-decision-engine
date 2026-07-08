import { apiFetch } from "./client";

export interface RiskData {
  risk_score: number;
  open_trades: number;
  max_open_trades: number;
  symbol_exposure: Record<string, number>;
  max_symbol_exposure: number;
  portfolio_exposure: number;
  max_portfolio_exposure: number;
  daily_loss: number;
  max_daily_loss: number;
  max_position_size_usd: number;
  account_equity: number;
  risk_per_trade_percent: number;
}

export interface PositionSizing {
  quantity: number;
  notional_value: number;
  risk_amount: number;
}

export function fetchRisk(): Promise<RiskData> {
  return apiFetch<RiskData>("/risk");
}

export function fetchPositionSizing(entry: number, atr: number): Promise<PositionSizing> {
  return apiFetch<PositionSizing>(`/position-sizing?entry=${entry}&atr=${atr}`);
}

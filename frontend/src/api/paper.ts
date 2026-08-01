import { apiFetch } from "./client";

export interface PaperTrade {
  id: number;
  symbol: string;
  side: string;
  entry: number;
  status: string;
  pnl: number | null;
  exit_price: number | null;
  close_reason: string | null;
  created_at: string | null;
  stop?: number;
  tp1?: number;
  tp2?: number;
  closed_at?: string | null;
}

export interface PaperPerformance {
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
}

export interface PaperTradingData {
  open: PaperTrade[];
  closed: PaperTrade[];
  performance: PaperPerformance;
}

export function fetchPaperTrading(): Promise<PaperTradingData> {
  return apiFetch<PaperTradingData>("/paper-trading");
}

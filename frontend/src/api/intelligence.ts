import { apiFetch } from "./client";

export interface IntelligenceData {
  market: {
    price?: number;
    regime?: string;
    btc_health?: number;
    volatility?: number;
    rsi?: number;
    error?: string;
  };
  signals: {
    total: number;
    open: number;
    approved: number;
    rejected: number;
  };
  risk: {
    open_trades: number;
    max_open_trades: number;
  };
  trades: {
    open: number;
    closed: number;
    total_pnl: number;
  };
}

export function fetchIntelligence(): Promise<IntelligenceData> {
  return apiFetch<IntelligenceData>("/intelligence");
}

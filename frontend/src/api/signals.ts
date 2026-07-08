import { apiFetch } from "./client";

export interface SignalRow {
  id: number;
  symbol: string;
  side: string;
  timeframe: string;
  price: number | null;
  confidence: number;
  decision: string;
  final_score: number;
  trend_score: number;
  volume_score: number;
  btc_score: number;
  risk_score: number;
  status: string;
  created_at: string | null;
}

export function fetchSignals(limit = 50): Promise<SignalRow[]> {
  return apiFetch<SignalRow[]>(`/signals?limit=${limit}`);
}

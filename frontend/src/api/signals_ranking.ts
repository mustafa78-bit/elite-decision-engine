import { apiFetch } from "./client";

export interface SignalRankingRow {
  rank: number;
  id: number;
  symbol: string;
  side: string;
  timeframe: string;
  score: number;
  confidence: number;
  decision: string;
  trend_score: number;
  volume_score: number;
  btc_score: number;
  risk_score: number;
  status: string;
  created_at: string | null;
}

export function fetchSignalsRanking(limit = 50): Promise<SignalRankingRow[]> {
  return apiFetch<SignalRankingRow[]>(`/signals/ranking?limit=${limit}`);
}

import { apiFetch } from "./client";

export interface MarketData {
  symbol: string;
  price: number;
  change_24h: number | null;
  regime: string;
  regime_score: number;
  volatility: number;
  volatility_score: number;
  btc_health_score: number;
  ema20: number;
  ema50: number;
  ema200: number;
  rsi: number;
  atr: number;
  error?: string;
}

export interface MarketLiveData {
  symbol: string;
  price: number;
  volume_24h: number;
  change_24h: number | null;
  high_24h: number;
  low_24h: number;
  timestamp: string;
  error?: string;
}

export function fetchMarket(): Promise<MarketData> {
  return apiFetch<MarketData>("/market");
}

export async function fetchMarketLive(symbol = "BTC"): Promise<MarketLiveData> {
  const res = await apiFetch<MarketLiveData & { error?: string }>(`/market/live?symbol=${encodeURIComponent(symbol)}`);
  if (res.error) throw new Error(res.error);
  return res;
}
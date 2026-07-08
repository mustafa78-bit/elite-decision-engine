import { apiFetch } from "./client";

export interface RegimeData {
  regime: string;
  trend: string;
  volatility_state: string;
  volatility: number;
  btc_health: number;
  rsi: number;
  ema20: number;
  ema50: number;
  ema200: number;
  error?: string;
}

export function fetchRegime(): Promise<RegimeData> {
  return apiFetch<RegimeData>("/regime");
}

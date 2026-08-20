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

export interface MarketLevel {
  price: number;
  type: "support" | "resistance";
  strength: number;
  touches: number;
}

export interface DivergencePoint {
  time: number;
  price: number;
  rsi: number;
}

export interface MarketDivergence {
  found: boolean;
  type: "bullish" | "bearish" | "none";
  p1: DivergencePoint | null;
  p2: DivergencePoint | null;
}

export interface ChannelPoint {
  time: number;
  price: number;
}

export interface ChannelBoundary {
  start: ChannelPoint;
  end: ChannelPoint;
}

export interface MarketChannel {
  found: boolean;
  direction: "up" | "down" | "sideways" | "none";
  upper: ChannelBoundary | null;
  lower: ChannelBoundary | null;
}

export interface LiquidityZone {
  price: number;
  type: "buy_side" | "sell_side";
  strength: number;
  touches: number;
}

export interface VolumeProfileBin {
  price_low: number;
  price_high: number;
  volume: number;
}

export interface VolumeProfile {
  bins: VolumeProfileBin[];
  poc_price: number | null;
  value_area_high: number | null;
  value_area_low: number | null;
}

export function fetchMarket(): Promise<MarketData> {
  return apiFetch<MarketData>("/market");
}

export async function fetchMarketLive(symbol = "BTC"): Promise<MarketLiveData> {
  const res = await apiFetch<MarketLiveData & { error?: string }>(`/market/live?symbol=${encodeURIComponent(symbol)}`);
  if (res.error) throw new Error(res.error);
  return res;
}

export async function fetchMarketLevels(symbol: string, timeframe: string): Promise<MarketLevel[]> {
  const res = await apiFetch<MarketLevel[] & { error?: string }>(
    `/market/levels?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`
  );
  if ("error" in res) throw new Error(res.error);
  return res;
}

export async function fetchMarketDivergence(symbol: string, timeframe: string): Promise<MarketDivergence> {
  const res = await apiFetch<MarketDivergence & { error?: string }>(
    `/market/divergence?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`
  );
  if (res.error) throw new Error(res.error);
  return res;
}

export async function fetchMarketChannel(symbol: string, timeframe: string): Promise<MarketChannel> {
  const res = await apiFetch<MarketChannel & { error?: string }>(
    `/market/channel?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`
  );
  if (res.error) throw new Error(res.error);
  return res;
}

export async function fetchLiquidityZones(symbol: string, timeframe: string): Promise<LiquidityZone[]> {
  const res = await apiFetch<LiquidityZone[] & { error?: string }>(
    `/market/liquidity-zones?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`
  );
  if ("error" in res) throw new Error(res.error);
  return res;
}

export async function fetchVolumeProfile(symbol: string, timeframe: string): Promise<VolumeProfile> {
  const res = await apiFetch<VolumeProfile & { error?: string }>(
    `/market/volume-profile?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`
  );
  if (res.error) throw new Error(res.error);
  return res;
}

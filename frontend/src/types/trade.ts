export type TradeEventType = "TRADE_OPENED" | "TRADE_CLOSED";

export interface TradeIntelligence {
  confidence: number;
  decision: string;
  final_score: number;
  trend_score: number;
  volume_score: number;
  btc_score: number;
  mtf_score: number;
  risk_score: number;
  rsi: number;
  ema20: number;
  ema50: number;
  ema200: number;
}

export interface TradePayload {
  trade_id?: number;
  symbol: string;
  side: string;
  entry: number;
  status: string;
  exit_price?: number;
  pnl?: number;
  close_reason?: string;
  intelligence?: TradeIntelligence;
}

export interface TradeNotification {
  event: TradeEventType;
  timestamp: string;
  payload: TradePayload;
}

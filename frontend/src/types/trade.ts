export type TradeEventType = "TRADE_OPENED" | "TRADE_CLOSED";

export type WsEventType = TradeEventType | "MARKET_UPDATE" | "SIGNAL_UPDATE" | "RISK_UPDATE";

export interface MarketPayload {
  price: number;
  regime: string;
  btc_health_score: number;
  volatility: number;
}

export interface SignalPayload {
  id: number;
  symbol: string;
  side: string;
  confidence: number;
  decision: string;
  final_score: number;
}

export interface RiskWsPayload {
  risk_score: number;
  open_trades: number;
  max_open_trades: number;
  daily_loss: number;
  max_daily_loss: number;
}

export interface WsEvent<T = unknown> {
  event: WsEventType;
  timestamp: string;
  payload: T;
}

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

export type TradeEventType = "TRADE_OPENED" | "TRADE_CLOSED";

export interface TradePayload {
  trade_id?: number;
  symbol: string;
  side: string;
  entry: number;
  status: string;
  exit_price?: number;
  pnl?: number;
  close_reason?: string;
}

export interface TradeNotification {
  event: TradeEventType;
  timestamp: string;
  payload: TradePayload;
}

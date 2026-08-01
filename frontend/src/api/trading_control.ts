import { apiFetch } from "./client";

export interface TradingControlData {
  exchanges: Array<{
    name: string;
    trading_enabled: boolean;
    status: string;
  }>;
  signals: {
    total: number;
    open: number;
    approved: number;
  };
  trades: {
    total: number;
    open: number;
    closed: number;
  };
  shadow: {
    mode: string;
    engine: string;
  };
  risk: {
    max_open_trades: number;
    max_daily_loss: number;
  };
}

export function fetchTradingControl(): Promise<TradingControlData> {
  return apiFetch<TradingControlData>("/trading-control");
}

import { Outlet, useLocation } from "react-router-dom";

import type { ConnectionStatus, WsRoomStatus } from "../../types/connection";
import type {
  CandleWsPayload,
  MarketPayload,
  PriceWsPayload,
  RiskWsPayload,
  SignalPayload,
  TradeIntelligence,
  TradeNotification,
  TradePayload,
  VolumeWsPayload,
} from "../../types/trade";
import Header from "./Header.tsx";
import IntelligencePanel from "../IntelligencePanel.tsx";
import Sidebar from "./Sidebar.tsx";

export interface LayoutContext {
  notifications: TradeNotification[];
  openTrades: TradePayload[];
  closedTrades: TradePayload[];
  latestIntelligence?: TradeIntelligence;
  latestMarket: MarketPayload | null;
  latestSignal: SignalPayload | null;
  latestRiskWs: RiskWsPayload | null;
  latestPrice: PriceWsPayload | null;
  latestCandle: CandleWsPayload | null;
  latestVolume: VolumeWsPayload | null;
}

interface Props {
  status: ConnectionStatus;
  wsRooms: WsRoomStatus;
  context: LayoutContext;
}

export default function Layout({ status, wsRooms, context }: Props) {
  const location = useLocation();
  const isDashboard = location.pathname === "/dashboard" || location.pathname === "/";

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-base)] text-[var(--text-primary)] font-mono text-sm">
      <Header status={status} wsRooms={wsRooms} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet context={context} />
        </main>
        {!isDashboard && (
          <aside className="w-72 h-full border-l border-[var(--border-subtle)] bg-[var(--bg-base)] shrink-0 overflow-y-auto hidden xl:block">
            <div className="p-3 space-y-3">
              <IntelligencePanel
                intelligence={context.latestIntelligence ?? {
                  confidence: 0,
                  decision: "PENDING",
                  final_score: 0,
                  trend_score: 0,
                  volume_score: 0,
                  btc_score: 0,
                  mtf_score: 0,
                  risk_score: 0,
                  rsi: 50,
                  ema20: 0,
                  ema50: 0,
                  ema200: 0,
                }}
              />
              <div className="widget-card">
                <div className="widget-header">
                  <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                    AI Summary
                  </span>
                </div>
                <div className="widget-body">
                  <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                    {context.latestIntelligence
                      ? `Decision: ${context.latestIntelligence.decision} | Confidence: ${(context.latestIntelligence.confidence * 100).toFixed(0)}%`
                      : "Awaiting signal data..."}
                  </p>
                </div>
              </div>
              <div className="widget-card">
                <div className="widget-header">
                  <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                    Market Pulse
                  </span>
                </div>
                <div className="widget-body space-y-2">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-[var(--text-muted)]">Price</span>
                    <span className="font-mono tabular-nums">
                      {context.latestPrice ? `$${context.latestPrice.price.toFixed(2)}` : "--"}
                    </span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-[var(--text-muted)]">24h Change</span>
                    <span className={`font-mono tabular-nums ${(context.latestPrice?.change_24h ?? 0) >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                      {context.latestPrice ? `${context.latestPrice.change_24h >= 0 ? "+" : ""}${context.latestPrice.change_24h.toFixed(2)}%` : "--"}
                    </span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-[var(--text-muted)]">Signal</span>
                    <span className={`font-mono tabular-nums ${context.latestSignal ? "text-[var(--accent-green)]" : "text-[var(--text-muted)]"}`}>
                      {context.latestSignal ? context.latestSignal.decision : "NONE"}
                    </span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-[var(--text-muted)]">Risk</span>
                    <span className="font-mono tabular-nums text-[var(--accent-yellow)]">
                      {context.latestRiskWs ? context.latestRiskWs.risk_score.toFixed(2) : "--"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

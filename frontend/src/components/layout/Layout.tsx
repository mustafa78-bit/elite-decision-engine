import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Room from "../room/Room.tsx";

import type { WsRoomStatus } from "../../types/connection";
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
  wsRooms: WsRoomStatus;
  context: LayoutContext;
}

export default function Layout({ wsRooms, context }: Props) {
  const { pathname } = useLocation();
  const price = context.latestPrice?.price ?? 0;
  const change24h = context.latestPrice?.change_24h ?? 0;
  const riskScore = context.latestRiskWs?.risk_score ?? 0;
  const confidence = context.latestIntelligence?.confidence ?? 0;
  const decision = context.latestIntelligence?.decision ?? "PENDING";
  const intelligence = context.latestIntelligence ?? {
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
  };

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-base)] text-[var(--text-primary)] font-sans text-sm select-none">
      <Header wsRooms={wsRooms} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6 bg-[#f8f9fc]">
          <Room>
            <AnimatePresence mode="wait">
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
                className="h-full"
              >
                <Outlet context={context} />
              </motion.div>
            </AnimatePresence>
          </Room>
        </main>

        {/* Right-Side Operations Telemetry Bar */}
        <aside className="w-72 h-full border-l border-[var(--border-default)] bg-white shrink-0 overflow-y-auto hidden xl:block shadow-[-4px_0_12px_rgba(15,23,42,0.01)]">
          <div className="p-5 space-y-5">
            <IntelligencePanel intelligence={intelligence} />

            <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-4 shadow-[0_1px_3px_rgba(15,23,42,0.01)]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  AI Summary
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              </div>
              <div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-medium">
                  {context.latestIntelligence
                    ? `Decision: ${decision} | Confidence: ${(confidence * 100).toFixed(0)}%`
                    : "Awaiting signal stream telemetry..."}
                </p>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-4 shadow-[0_1px_3px_rgba(15,23,42,0.01)]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  Market Pulse
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              </div>
              <div className="space-y-2.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[var(--text-secondary)] font-medium">Price</span>
                  <span className="font-mono font-bold text-slate-800 tabular-nums">
                    {context.latestPrice ? `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "--"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs border-t border-slate-200/40 pt-2">
                  <span className="text-[var(--text-secondary)] font-medium">24h Change</span>
                  <span className={`font-mono font-bold tabular-nums ${change24h >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                    {context.latestPrice ? `${change24h >= 0 ? "+" : ""}${change24h.toFixed(2)}%` : "--"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs border-t border-slate-200/40 pt-2">
                  <span className="text-[var(--text-secondary)] font-medium">Signal</span>
                  <span className={`font-mono font-bold tabular-nums ${context.latestSignal ? "text-emerald-600" : "text-[var(--text-muted)]"}`}>
                    {context.latestSignal ? context.latestSignal.decision : "NONE"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs border-t border-slate-200/40 pt-2">
                  <span className="text-[var(--text-secondary)] font-medium">Risk Score</span>
                  <span className="font-mono font-bold tabular-nums text-amber-600">
                    {context.latestRiskWs ? riskScore.toFixed(2) : "--"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

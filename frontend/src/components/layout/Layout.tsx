import { Outlet, useLocation, useNavigate, Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useUIStore } from "../../stores/ui-store";
import { useAuth } from "../auth/AuthProvider";
import {
  Search,
  Bell,
  User,
  LogOut,
  TrendingUp,
  TrendingDown,
  Globe,
} from "lucide-react";
import Sidebar from "./Sidebar";
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
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { setCommandPaletteOpen } = useUIStore();

  const price = context.latestPrice?.price ?? 65420.0;
  const change24h = context.latestPrice?.change_24h ?? 2.45;

  return (
    <div className="h-screen flex flex-col bg-slate-50 text-slate-900 overflow-hidden font-sans">
      {/* TopBar 64px */}
      <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0 z-20">
        <div className="flex items-center gap-8">
          {/* Logo / Branding */}
          <Link to="/overview" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-extrabold text-base tracking-widest">
              Φ
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold text-slate-900 tracking-tight leading-none">
                ELITE
              </span>
              <span className="text-[9px] text-blue-600 font-semibold tracking-widest uppercase">
                TERMINAL
              </span>
            </div>
          </Link>

          {/* Institutional Universal Search */}
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-400 hover:text-slate-600 hover:border-slate-300 transition-all w-64 text-left"
          >
            <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="flex-1">Universal Search...</span>
            <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-slate-200 border border-slate-300 text-slate-500">
              Ctrl+K
            </span>
          </button>
        </div>

        {/* Real-time Ticker & Actions */}
        <div className="flex items-center gap-6">
          {/* Market Ticker */}
          <div className="flex items-center gap-4 border-l border-slate-200 pl-4 h-8">
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  BTC/USDT
                </span>
                {change24h >= 0 ? (
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                ) : (
                  <TrendingDown className="w-3.5 h-3.5 text-rose-600" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold font-mono text-slate-900 leading-none">
                  ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span
                  className={`text-[10px] font-bold font-mono px-1 rounded ${
                    change24h >= 0 ? "text-emerald-700 bg-emerald-50" : "text-rose-700 bg-rose-50"
                  }`}
                >
                  {change24h >= 0 ? "+" : ""}
                  {change24h.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          {/* Core Feeds System Health Indicator */}
          <div className="hidden lg:flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5">
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            <div className="flex gap-1">
              {Object.entries(wsRooms).map(([room, status]) => (
                <span
                  key={room}
                  className={`w-1.5 h-1.5 rounded-full ${
                    status === "CONNECTED" ? "bg-emerald-500" : "bg-rose-400"
                  }`}
                  title={`${room}: ${status}`}
                />
              ))}
            </div>
          </div>

          {/* Action Icons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/notifications")}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors relative"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              {context.notifications.length > 0 && (
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-rose-500 rounded-full" />
              )}
            </button>

            <button
              onClick={() => navigate("/profile")}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors"
              title="Profile"
            >
              <User className="w-4 h-4" />
            </button>

            <button
              onClick={() => logout()}
              className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Frame */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Content Shell */}
        <main className="flex-1 overflow-y-auto bg-slate-50 flex flex-col focus:outline-none">
          <div className="flex-1 w-full max-w-[1440px] mx-auto px-8 py-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="h-full"
              >
                <Outlet context={context} />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}

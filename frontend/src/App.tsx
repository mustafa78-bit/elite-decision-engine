import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/layout/Layout";
import { LoadingScreen } from "./components/layout/LoadingScreen";
import { ThemeProvider } from "./components/theme/ThemeProvider";
import { AuthProvider, useAuth } from "./components/auth/AuthProvider";
import { AuthGuard } from "./components/auth/AuthGuard";
import { apiFetch } from "./api/client";
import type {
  CandleWsPayload,
  MarketPayload,
  PriceWsPayload,
  RiskWsPayload,
  SignalPayload,
  TradeNotification,
  TradePayload,
  VolumeWsPayload,
  WsEvent,
} from "./types/trade";
import {
  connectTradesSocket,
} from "./websocket/client";
import type { ConnectionStatus, WsRoomStatus } from "./types/connection";

const Analytics = lazy(() => import("./pages/Analytics"));
const AssetDetail = lazy(() => import("./pages/AssetDetail"));
const Backtest = lazy(() => import("./pages/Backtest"));
const CommandDeck = lazy(() => import("./pages/CommandDeck"));
const DecisionCenter = lazy(() => import("./pages/DecisionCenter"));
const Execution = lazy(() => import("./pages/Execution"));
const Intelligence = lazy(() => import("./pages/Intelligence"));
const Journal = lazy(() => import("./pages/Journal"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const ChartEmbed = lazy(() => import("./pages/ChartEmbed"));
const Market = lazy(() => import("./pages/Market"));
const NotFound = lazy(() => import("./pages/NotFound"));
const NotificationsPage = lazy(() => import("./pages/Notifications"));
const Overview = lazy(() => import("./pages/Overview"));
const PaperTrading = lazy(() => import("./pages/PaperTrading"));
const Portfolio = lazy(() => import("./pages/Portfolio"));
const Profile = lazy(() => import("./pages/Profile"));
const Regime = lazy(() => import("./pages/Regime"));
const Risk = lazy(() => import("./pages/Risk"));
const Scanner = lazy(() => import("./pages/Scanner"));
const Signals = lazy(() => import("./pages/Signals"));
const Trades = lazy(() => import("./pages/Trades"));
const TradingControl = lazy(() => import("./pages/TradingControl"));
const PreferencesPage = lazy(() => import("./pages/PreferencesPage"));
const TimelinePage = lazy(() => import("./pages/TimelinePage"));
const WatchlistsPage = lazy(() => import("./pages/WatchlistsPage"));
const FundingPage = lazy(() => import("./pages/FundingPage"));
const OpenInterestPage = lazy(() => import("./pages/OpenInterestPage"));
const HeroDashboard = lazy(() => import("./pages/HeroDashboard"));
const TradingWorkspace = lazy(() => import("./pages/TradingWorkspace"));
const MarketSimulator = lazy(() => import("./pages/MarketSimulator"));

const MAX_EVENTS = 100;

export function AppRoutes() {
  const [notifications, setNotifications] = useState<TradeNotification[]>([]);
  const [openTrades, setOpenTrades] = useState<TradePayload[]>([]);
  const [closedTrades, setClosedTrades] = useState<TradePayload[]>([]);
  const [latestMarket, setLatestMarket] = useState<MarketPayload | null>(null);
  const [latestSignal, setLatestSignal] = useState<SignalPayload | null>(null);
  const [latestRiskWs, setLatestRiskWs] = useState<RiskWsPayload | null>(null);
  const [latestPrice, setLatestPrice] = useState<PriceWsPayload | null>(null);
  const [latestCandle, setLatestCandle] = useState<CandleWsPayload | null>(null);
  const [latestVolume, setLatestVolume] = useState<VolumeWsPayload | null>(null);
  const [wsRooms, setWsRooms] = useState<WsRoomStatus>({
    trades: "DISCONNECTED",
    analytics: "DISCONNECTED",
    portfolio: "DISCONNECTED",
    notifications: "DISCONNECTED",
    preferences: "DISCONNECTED",
  });
  const { token } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    interface PositionRow {
      id: number;
      symbol: string;
      side: string;
      entry: number;
      stop: number | null;
      tp1: number | null;
      tp2: number | null;
      status: string;
      pnl: number | null;
      exit_price: number | null;
      close_reason: string | null;
    }

    // Trades opened before this page load only ever reach openTrades/
    // closedTrades via TRADE_OPENED/TRADE_CLOSED websocket events below --
    // there was no initial hydration, so a fresh page load or hard refresh
    // showed zero open trades until a *new* trade event happened to arrive
    // during that session, even though the account genuinely had open
    // positions. /paper/positions already returns the real Trade rows
    // (entry/stop/tp1/tp2/status/pnl) this app needs -- fetch once here to
    // seed both lists before/alongside the live websocket connection.
    apiFetch<{ positions: PositionRow[] }>("/paper/positions?limit=200")
      .then((res) => {
        if (cancelled) return;
        const mapped: TradePayload[] = res.positions.map((p) => ({
          trade_id: p.id,
          symbol: p.symbol,
          side: p.side,
          entry: p.entry,
          stop: p.stop ?? undefined,
          tp1: p.tp1 ?? undefined,
          tp2: p.tp2 ?? undefined,
          status: p.status,
          exit_price: p.exit_price ?? undefined,
          pnl: p.pnl ?? undefined,
          close_reason: p.close_reason ?? undefined,
        }));
        setOpenTrades(mapped.filter((t) => t.status === "OPEN"));
        setClosedTrades(mapped.filter((t) => t.status !== "OPEN"));
      })
      .catch(() => {
        // Live websocket updates still work without this hydration --
        // just no pre-existing trades to show until the next live event.
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    let retryCount = 0;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    const MAX_RETRIES = 10;
    const RETRY_INTERVAL_MS = 3000;

    const handleMessage = (data: WsEvent) => {
      if (data.event === "TRADE_OPENED" || data.event === "TRADE_CLOSED") {
        const p = data.payload as unknown as TradePayload;
        const ts = data.timestamp;
        setNotifications((prev) => {
          const next = [...prev, { event: data.event, timestamp: ts, payload: p } as TradeNotification];
          return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
        });

        if (data.event === "TRADE_OPENED") {
          setOpenTrades((prev) =>
            prev.some((t) => t.trade_id === p.trade_id) ? prev : [...prev, p],
          );
        }

        if (data.event === "TRADE_CLOSED") {
          setOpenTrades((prev) =>
            prev.filter((t) => t.trade_id !== p.trade_id),
          );
          setClosedTrades((prev) => [...prev, p]);
        }
      }

      if (data.event === "MARKET_UPDATE") {
        setLatestMarket(data.payload as MarketPayload);
      }

      if (data.event === "SIGNAL_UPDATE") {
        setLatestSignal(data.payload as SignalPayload);
      }

      if (data.event === "RISK_UPDATE") {
        setLatestRiskWs(data.payload as RiskWsPayload);
      }

      if (data.event === "PRICE_UPDATE") {
        setLatestPrice(data.payload as PriceWsPayload);
      }

      if (data.event === "CANDLE_UPDATE") {
        setLatestCandle(data.payload as CandleWsPayload);
      }

      if (data.event === "VOLUME_UPDATE") {
        setLatestVolume(data.payload as VolumeWsPayload);
      }
    };

    const handleStatus = (s: ConnectionStatus) => {
      setWsRooms((prev) => ({ ...prev, trades: s }));
      if (s === "CONNECTED") {
        retryCount = 0;
      } else if (s === "DISCONNECTED" && !cancelled && retryCount < MAX_RETRIES) {
        retryCount += 1;
        retryTimer = setTimeout(connect, RETRY_INTERVAL_MS);
      }
    };

    function connect() {
      if (cancelled) return;
      wsRef.current = connectTradesSocket(handleMessage, handleStatus);
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [token]);

  const latestIntelligence = [...notifications]
    .reverse()
    .find((n) => n.payload.intelligence)
    ?.payload.intelligence;

  const outletContext = {
    notifications,
    openTrades,
    closedTrades,
    latestIntelligence,
    latestMarket,
    latestSignal,
    latestRiskWs,
    latestPrice,
    latestCandle,
    latestVolume,
  };

  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
      <Routes>
        <Route path="/" element={<Navigate to="/command-deck" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/embed/chart" element={<ChartEmbed />} />

        <Route
          element={
            <AuthGuard>
              <Layout wsRooms={wsRooms} context={outletContext} />
            </AuthGuard>
          }
        >
          <Route path="/command-deck" element={<CommandDeck />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/dashboard" element={<Navigate to="/command-deck" replace />} />
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/decisions" element={<DecisionCenter />} />
          <Route path="/asset/:symbol" element={<AssetDetail />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/watchlists" element={<WatchlistsPage />} />
          <Route path="/portfolio-detail" element={<Navigate to="/portfolio" replace />} />
          <Route path="/market" element={<Market />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/signals/ranking" element={<Navigate to="/signals" replace />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/regime" element={<Regime />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/paper-trading" element={<PaperTrading />} />
          <Route path="/execution" element={<Execution />} />
          <Route path="/intelligence" element={<Intelligence />} />
          <Route path="/live-market" element={<Navigate to="/market" replace />} />
          <Route path="/trading-control" element={<TradingControl />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/preferences" element={<PreferencesPage />} />
          <Route path="/funding" element={<FundingPage />} />
          <Route path="/open-interest" element={<OpenInterestPage />} />
          <Route path="/whale" element={<Navigate to="/command-deck" replace />} />
          <Route path="/liquidity" element={<Navigate to="/command-deck" replace />} />
          <Route path="/hero-dashboard" element={<HeroDashboard />} />
          <Route path="/trading-workspace" element={<TradingWorkspace />} />
          <Route path="/ai-experience" element={<Navigate to="/command-deck" replace />} />
          <Route path="/simulator" element={<MarketSimulator />} />
          <Route path="/professional-workspace" element={<Navigate to="/execution" replace />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

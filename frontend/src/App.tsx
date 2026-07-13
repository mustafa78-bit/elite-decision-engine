import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/layout/Layout";
import Analytics from "./pages/Analytics";
import AssetDetail from "./pages/AssetDetail";
import Backtest from "./pages/Backtest";
import Dashboard from "./pages/Dashboard";
import DecisionCenter from "./pages/DecisionCenter";
import Execution from "./pages/Execution";
import Intelligence from "./pages/Intelligence";
import Journal from "./pages/Journal";
import LoginPage from "./pages/LoginPage";
import Market from "./pages/Market";
import NotFound from "./pages/NotFound";
import NotificationsPage from "./pages/Notifications";
import Overview from "./pages/Overview";
import PaperTrading from "./pages/PaperTrading";
import Portfolio from "./pages/Portfolio";
import Profile from "./pages/Profile";
import Regime from "./pages/Regime";
import Risk from "./pages/Risk";
import Scanner from "./pages/Scanner";
import Signals from "./pages/Signals";
import SignalsRanking from "./pages/SignalsRanking";
import Trades from "./pages/Trades";
import TradingControl from "./pages/TradingControl";
import LiveMarket from "./pages/LiveMarket";
import PreferencesPage from "./pages/PreferencesPage";
import TimelinePage from "./pages/TimelinePage";
import WatchlistsPage from "./pages/WatchlistsPage";
import PortfolioDetailPage from "./pages/PortfolioDetailPage";
import FundingPage from "./pages/FundingPage";
import OpenInterestPage from "./pages/OpenInterestPage";
import WhalePage from "./pages/WhalePage";
import LiquidityPage from "./pages/LiquidityPage";
import HeroDashboard from "./pages/HeroDashboard";
import TradingWorkspace from "./pages/TradingWorkspace";
import AIExperience from "./pages/AIExperience";
import ProfessionalWorkspace from "./pages/ProfessionalWorkspace";
import { ThemeProvider } from "./components/theme/ThemeProvider";
import { AuthProvider } from "./components/auth/AuthProvider";
import { AuthGuard } from "./components/auth/AuthGuard";
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

const MAX_EVENTS = 100;

function App() {
  const [notifications, setNotifications] = useState<TradeNotification[]>([]);
  const [openTrades, setOpenTrades] = useState<TradePayload[]>([]);
  const [closedTrades, setClosedTrades] = useState<TradePayload[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
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
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) return;
    wsRef.current = connectTradesSocket(
      (data: WsEvent) => {
        if (data.event === "TRADE_OPENED" || data.event === "TRADE_CLOSED") {
          const p = data.payload as unknown as TradePayload;
          const ts = data.timestamp;
          setNotifications((prev) => {
            const next = [...prev, { event: data.event, timestamp: ts, payload: p } as TradeNotification];
            return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
          });

          if (data.event === "TRADE_OPENED") {
            setOpenTrades((prev) => [...prev, p]);
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
      },
      (s) => {
        setStatus(s);
        setWsRooms((prev) => ({ ...prev, trades: s }));
      },
    );
    return () => wsRef.current?.close();
  }, []);

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
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<LoginPage />} />

            <Route
              element={
                <AuthGuard>
                  <Layout status={status} wsRooms={wsRooms} context={outletContext} />
                </AuthGuard>
              }
            >
              <Route path="/overview" element={<Overview />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/decisions" element={<DecisionCenter />} />
              <Route path="/asset/:symbol" element={<AssetDetail />} />
              <Route path="/profile" element={<Profile />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/watchlists" element={<WatchlistsPage />} />
          <Route path="/portfolio-detail" element={<PortfolioDetailPage />} />
          <Route path="/market" element={<Market />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/signals/ranking" element={<SignalsRanking />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/regime" element={<Regime />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/paper-trading" element={<PaperTrading />} />
          <Route path="/execution" element={<Execution />} />
          <Route path="/intelligence" element={<Intelligence />} />
          <Route path="/live-market" element={<LiveMarket />} />
          <Route path="/trading-control" element={<TradingControl />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/preferences" element={<PreferencesPage />} />
          <Route path="/funding" element={<FundingPage />} />
          <Route path="/open-interest" element={<OpenInterestPage />} />
          <Route path="/whale" element={<WhalePage />} />
          <Route path="/liquidity" element={<LiquidityPage />} />
          <Route path="/hero-dashboard" element={<HeroDashboard />} />
          <Route path="/trading-workspace" element={<TradingWorkspace />} />
          <Route path="/ai-experience" element={<AIExperience />} />
          <Route path="/professional-workspace" element={<ProfessionalWorkspace />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
    </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

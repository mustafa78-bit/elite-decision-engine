import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/layout/Layout";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import Market from "./pages/Market";
import Overview from "./pages/Overview";
import Risk from "./pages/Risk";
import Signals from "./pages/Signals";
import Trades from "./pages/Trades";
import type {
  MarketPayload,
  RiskWsPayload,
  SignalPayload,
  TradeNotification,
  TradePayload,
  WsEvent,
} from "./types/trade";
import { connectTradesSocket } from "./websocket/client";
import type { ConnectionStatus } from "./types/connection";

const MAX_EVENTS = 100;

function App() {
  const [notifications, setNotifications] = useState<TradeNotification[]>([]);
  const [openTrades, setOpenTrades] = useState<TradePayload[]>([]);
  const [closedTrades, setClosedTrades] = useState<TradePayload[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const [latestMarket, setLatestMarket] = useState<MarketPayload | null>(null);
  const [latestSignal, setLatestSignal] = useState<SignalPayload | null>(null);
  const [latestRiskWs, setLatestRiskWs] = useState<RiskWsPayload | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
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
      },
      (s) => setStatus(s),
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
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route element={<Layout status={status} context={outletContext} />}>
          <Route path="/overview" element={<Overview />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/market" element={<Market />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

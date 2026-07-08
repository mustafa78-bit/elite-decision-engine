import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/layout/Layout";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import Market from "./pages/Market";
import Risk from "./pages/Risk";
import Signals from "./pages/Signals";
import Trades from "./pages/Trades";
import type { TradeNotification, TradePayload } from "./types/trade";
import { connectTradesSocket } from "./websocket/client";
import type { ConnectionStatus } from "./websocket/client";

const MAX_EVENTS = 100;

function App() {
  const [notifications, setNotifications] = useState<TradeNotification[]>([]);
  const [openTrades, setOpenTrades] = useState<TradePayload[]>([]);
  const [closedTrades, setClosedTrades] = useState<TradePayload[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    wsRef.current = connectTradesSocket(
      (data) => {
        setNotifications((prev) => {
          const next = [...prev, data];
          return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
        });

        if (data.event === "TRADE_OPENED") {
          setOpenTrades((prev) => [...prev, data.payload]);
        }

        if (data.event === "TRADE_CLOSED") {
          setOpenTrades((prev) =>
            prev.filter((t) => t.trade_id !== data.payload.trade_id),
          );
          setClosedTrades((prev) => [...prev, data.payload]);
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
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route element={<Layout status={status} context={outletContext} />}>
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

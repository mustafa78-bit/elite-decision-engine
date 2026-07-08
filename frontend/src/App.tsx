import { useEffect, useRef, useState } from "react";

import ClosedTrades from "./components/ClosedTrades";
import DashboardStats from "./components/DashboardStats";
import IntelligencePanel from "./components/IntelligencePanel";
import OpenTrades from "./components/OpenTrades";
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

  const statusColor =
    status === "CONNECTED" ? "bg-green-500" : "bg-red-500";

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 font-mono text-sm">
      <header className="mb-4 flex items-center justify-between border-b border-gray-800 pb-3">
        <div>
          <h1 className="text-lg font-semibold tracking-wide">
            Elite Decision Engine
          </h1>
          <p className="text-[10px] text-gray-500 uppercase tracking-widest">
            Trading Dashboard
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${statusColor}`} />
          <span className="text-[10px] text-gray-500 uppercase">{status}</span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <DashboardStats notifications={notifications} />

          <section>
            <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-2">
              Open Trades
            </h2>
            <OpenTrades trades={openTrades} />
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-2">
              Closed Trades
            </h2>
            <ClosedTrades trades={closedTrades} />
          </section>
        </div>

        {latestIntelligence && (
          <div className="lg:col-span-1">
            <IntelligencePanel intelligence={latestIntelligence} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

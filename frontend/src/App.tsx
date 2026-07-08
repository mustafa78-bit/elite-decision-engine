import { useEffect, useRef, useState } from "react";

import TradePanel from "./components/TradePanel";
import type { TradeNotification } from "./types/trade";
import { connectTradesSocket } from "./websocket/client";
import type { ConnectionStatus } from "./websocket/client";

const MAX_EVENTS = 50;

function App() {
  const [notifications, setNotifications] = useState<TradeNotification[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    wsRef.current = connectTradesSocket(
      (data) => {
        setNotifications((prev) => {
          const next = [...prev, data];
          return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
        });
      },
      (s) => setStatus(s),
    );
    return () => wsRef.current?.close();
  }, []);

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
            Live Trade Feed
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${statusColor}`} />
          <span className="text-[10px] text-gray-500 uppercase">{status}</span>
        </div>
      </header>
      <main>
        <TradePanel notifications={notifications} />
      </main>
    </div>
  );
}

export default App;

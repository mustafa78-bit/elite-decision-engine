import { useEffect, useState } from "react";

import TradePanel from "./components/TradePanel";
import type { TradeNotification } from "./types/trade";
import { connectTradesSocket } from "./websocket/client";

function App() {
  const [notifications, setNotifications] = useState<TradeNotification[]>([]);

  useEffect(() => {
    const ws = connectTradesSocket((data) => {
      setNotifications((prev) => [...prev, data]);
    });
    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Elite Decision Engine</h1>
        <p className="text-sm text-gray-400">Live trade feed</p>
      </header>
      <main>
        <TradePanel notifications={notifications} />
      </main>
    </div>
  );
}

export default App;

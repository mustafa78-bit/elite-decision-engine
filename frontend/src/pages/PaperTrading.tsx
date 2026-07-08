import { useCallback, useEffect, useState } from "react";

import type { PaperTradingData } from "../api/paper";
import { fetchPaperTrading } from "../api/paper";
import { ApiError } from "../api/client";
import PaperPnLCard from "../components/paper/PaperPnLCard";
import PaperPerformanceCard from "../components/paper/PaperPerformanceCard";
import PaperPositionTable from "../components/paper/PaperPositionTable";

export default function PaperTrading() {
  const [data, setData] = useState<PaperTradingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchPaperTrading();
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load paper trading");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading paper trading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        No paper trading data
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">Paper Trading Terminal</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PaperPnLCard
          totalPnl={data.performance.total_pnl}
          openTrades={data.performance.open_trades}
          closedTrades={data.performance.closed_trades}
        />
        <PaperPerformanceCard
          totalTrades={data.performance.total_trades}
          winningTrades={data.performance.winning_trades}
          losingTrades={data.performance.losing_trades}
          winRate={data.performance.win_rate}
        />
      </div>

      <PaperPositionTable trades={data.open} title="Open Trades" />
      <PaperPositionTable trades={data.closed} title="Closed Trades" />
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";

import type { IntelligenceData } from "../api/intelligence";
import { fetchIntelligence } from "../api/intelligence";
import { ApiError } from "../api/client";
import MarketOverview from "../components/intelligence/MarketOverview";
import SignalFeed from "../components/intelligence/SignalFeed";
import RiskMonitor from "../components/intelligence/RiskMonitor";
import TradeMonitor from "../components/intelligence/TradeMonitor";

export default function Intelligence() {
  const [data, setData] = useState<IntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchIntelligence();
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load intelligence");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading intelligence dashboard...
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

  if (!data) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">Live Intelligence Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MarketOverview
          price={data.market.price}
          regime={data.market.regime}
          btcHealth={data.market.btc_health}
          volatility={data.market.volatility}
          rsi={data.market.rsi}
        />
        <SignalFeed
          total={data.signals.total}
          open={data.signals.open}
          approved={data.signals.approved}
          rejected={data.signals.rejected}
        />
        <RiskMonitor
          openTrades={data.risk.open_trades}
          maxOpenTrades={data.risk.max_open_trades}
        />
        <TradeMonitor
          open={data.trades.open}
          closed={data.trades.closed}
          totalPnl={data.trades.total_pnl}
        />
      </div>
    </div>
  );
}

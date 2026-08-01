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
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading intelligence dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Live Intelligence Dashboard</h2>

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

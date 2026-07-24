import { useCallback, useEffect, useState } from "react";

import type { IntelligenceData } from "../api/intelligence";
import { fetchIntelligence } from "../api/intelligence";
import { ApiError } from "../api/client";
import MarketOverview from "../components/intelligence/MarketOverview";
import SignalFeed from "../components/intelligence/SignalFeed";
import RiskMonitor from "../components/intelligence/RiskMonitor";
import TradeMonitor from "../components/intelligence/TradeMonitor";
import { PageHeader } from "../components/ui/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";

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
      <div className="space-y-4">
        <PageHeader
          title="Live Intelligence Dashboard"
          subtitle="Aggregated real-time system, market, and signal parameters"
        />
        <EmptyState
          loading
          title="Loading intelligence parameters..."
          description="Synthesizing telemetry across core AI consensus layers, portfolios, and risk boundaries."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Live Intelligence Dashboard"
          subtitle="Aggregated real-time system, market, and signal parameters"
        />
        <EmptyState
          title="No intelligence telemetry available"
          description="The aggregated telemetry intelligence engine is currently offline or loading. Reconnect or try again shortly."
          error={error}
          actionButton={{
            label: "Retry connection",
            onClick: load,
          }}
        />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Live Intelligence Dashboard"
        subtitle="Aggregated real-time system, market, and signal parameters"
      />

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

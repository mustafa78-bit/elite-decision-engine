import { useCallback, useEffect, useState } from "react";

import type { IntelligenceData } from "../api/intelligence";
import { fetchIntelligence } from "../api/intelligence";
import { ApiError } from "../api/client";
import MarketOverview from "../components/intelligence/MarketOverview";
import SignalFeed from "../components/intelligence/SignalFeed";
import RiskMonitor from "../components/intelligence/RiskMonitor";
import TradeMonitor from "../components/intelligence/TradeMonitor";
import { LoadingScreen } from "../components/layout/LoadingScreen";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader, PageContainer } from "../components/ui/PageHeader";

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
      <PageContainer>
        <PageHeader title="Intelligence" subtitle="Live Intelligence Dashboard" />
        <LoadingScreen variant="grid" />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <PageHeader title="Intelligence" subtitle="Live Intelligence Dashboard" />
        <ErrorState message={error} onRetry={load} />
      </PageContainer>
    );
  }

  if (!data) {
    return (
      <PageContainer>
        <PageHeader title="Intelligence" subtitle="Live Intelligence Dashboard" />
        <EmptyState
          title="No Intelligence Data"
          description="Check connection to live intelligence subsystem."
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader title="Intelligence" subtitle="Live Intelligence Dashboard" />

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
    </PageContainer>
  );
}

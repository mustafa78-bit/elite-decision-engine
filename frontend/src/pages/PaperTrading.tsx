import { useCallback, useEffect, useState } from "react";

import type { PaperTradingData } from "../api/paper";
import { fetchPaperTrading } from "../api/paper";
import { ApiError } from "../api/client";
import PaperPnLCard from "../components/paper/PaperPnLCard";
import PaperPerformanceCard from "../components/paper/PaperPerformanceCard";
import PaperPositionTable from "../components/paper/PaperPositionTable";
import { LoadingScreen } from "../components/layout/LoadingScreen";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader, PageContainer } from "../components/ui/PageHeader";

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
      <PageContainer>
        <PageHeader title="Paper Trading" subtitle="Simulated Live Trading Environment" />
        <LoadingScreen variant="grid" />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <PageHeader title="Paper Trading" subtitle="Simulated Live Trading Environment" />
        <ErrorState message={error} onRetry={load} />
      </PageContainer>
    );
  }

  if (!data) {
    return (
      <PageContainer>
        <PageHeader title="Paper Trading" subtitle="Simulated Live Trading Environment" />
        <EmptyState
          title="No Paper Trading Profile"
          description="Simulated execution history and paper account stats are currently not loaded."
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader title="Paper Trading" subtitle="Simulated Live Trading Environment" />

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
    </PageContainer>
  );
}

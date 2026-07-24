import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";

import type { LayoutContext } from "../components/layout/Layout";
import type { PortfolioStats } from "../api/portfolio";
import { fetchPortfolio } from "../api/portfolio";
import { ApiError } from "../api/client";
import BalanceCard from "../components/portfolio/BalanceCard";
import ExposureChart from "../components/portfolio/ExposureChart";
import AllocationCard from "../components/portfolio/AllocationCard";
import PositionTable from "../components/portfolio/PositionTable";
import MetricCard from "../components/MetricCard";
import { PageHeader } from "../components/ui/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";

export default function Portfolio() {
  const { openTrades } = useOutletContext<LayoutContext>();
  const [port, setPort] = useState<PortfolioStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchPortfolio();
      setPort(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Portfolio Terminal"
          subtitle="Real-time equity, allocations, exposure, and performance metrics"
        />
        <EmptyState
          loading
          title="Loading portfolio telemetry..."
          description="Fetching balance distributions and historical performance curves."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Portfolio Terminal"
          subtitle="Real-time equity, allocations, exposure, and performance metrics"
        />
        <EmptyState
          title="No portfolio telemetry available"
          description="The portfolio service is currently offline. Reconnect or try again shortly."
          error={error}
          actionButton={{
            label: "Retry connection",
            onClick: load,
          }}
        />
      </div>
    );
  }

  if (!port) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Portfolio Terminal"
          subtitle="Real-time equity, allocations, exposure, and performance metrics"
        />
        <EmptyState
          title="No portfolio data available"
          description="The current user account has no active assets or historical trading distribution records."
        />
      </div>
    );
  }

  const positions = openTrades.map((t) => ({
    symbol: t.symbol,
    side: t.side,
    entry: t.entry,
    status: t.status,
    pnl: t.pnl,
  }));

  return (
    <div className="space-y-4">
      <PageHeader
        title="Portfolio Terminal"
        subtitle="Real-time equity, allocations, exposure, and performance metrics"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <BalanceCard
          equity={port.equity}
          totalPnl={port.total_pnl}
          unrealizedPnl={port.unrealized_pnl}
        />
        <div className="grid grid-cols-2 gap-3">
          <MetricCard label="Win Rate" value={`${port.win_rate.toFixed(1)}%`} />
          <MetricCard label="Loss Rate" value={`${port.loss_rate.toFixed(1)}%`} negative />
          <MetricCard label="Total Trades" value={String(port.total_trades)} />
          <MetricCard label="Avg PnL" value={`$${port.average_pnl.toFixed(2)}`} positive={port.average_pnl >= 0} negative={port.average_pnl < 0} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard label="Profit Factor" value={port.profit_factor.toFixed(2)} />
          <MetricCard label="Max Drawdown" value={`${port.max_drawdown.toFixed(1)}%`} negative />
          <MetricCard label="Open Exposure" value={`$${port.current_open_exposure.toFixed(0)}`} />
          <MetricCard label="Daily PnL" value={`$${port.daily_pnl.toFixed(2)}`} positive={port.daily_pnl >= 0} negative={port.daily_pnl < 0} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ExposureChart allocation={port.allocation} />
        <AllocationCard allocation={port.allocation} />
      </div>

      <PositionTable positions={positions} />
    </div>
  );
}

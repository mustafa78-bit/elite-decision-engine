import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";

import type { LayoutContext } from "../components/layout/Layout";
import type { PortfolioStats } from "../api/portfolio";
import { fetchPortfolio } from "../api/portfolio";
import { ApiError } from "../api/client";
import BalanceCard from "../components/portfolio/BalanceCard";
import ExposureChart from "../components/portfolio/ExposureChart";
import AllocationCard from "../components/portfolio/AllocationCard";
import PositionTable from "../components/portfolio/PositionTable";
import MetricCard from "../components/MetricCard";

export default function Portfolio() {
  const { t } = useTranslation(["portfolio", "common"]);
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
      setError(e instanceof ApiError ? e.message : t("page.loadError"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("page.loading")}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)] bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            {t("common:retry")}
          </button>
        </div>
      </div>
    );
  }

  if (!port) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("page.noData")}
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
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        {t("page.heading")}
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <BalanceCard
          equity={port.equity}
          totalPnl={port.total_pnl}
          unrealizedPnl={port.unrealized_pnl}
        />
        <div className="grid grid-cols-2 gap-3">
          <MetricCard label={t("page.metrics.winRate")} value={`${port.win_rate.toFixed(1)}%`} />
          <MetricCard label={t("page.metrics.lossRate")} value={`${port.loss_rate.toFixed(1)}%`} negative />
          <MetricCard label={t("page.metrics.totalTrades")} value={String(port.total_trades)} />
          <MetricCard label={t("page.metrics.avgPnl")} value={`$${port.average_pnl.toFixed(2)}`} positive={port.average_pnl >= 0} negative={port.average_pnl < 0} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard label={t("page.metrics.profitFactor")} value={port.profit_factor.toFixed(2)} />
          <MetricCard label={t("page.metrics.maxDrawdown")} value={`${port.max_drawdown.toFixed(1)}%`} negative />
          <MetricCard label={t("page.metrics.openExposure")} value={`$${port.current_open_exposure.toFixed(0)}`} />
          <MetricCard label={t("page.metrics.dailyPnl")} value={`$${port.daily_pnl.toFixed(2)}`} positive={port.daily_pnl >= 0} negative={port.daily_pnl < 0} />
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

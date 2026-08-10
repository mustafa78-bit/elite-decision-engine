import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import DrawdownChart from "../components/charts/DrawdownChart";
import MetricCard from "../components/MetricCard";
import PerformanceChart from "../components/charts/PerformanceChart";
import PerformanceSummary from "../components/charts/PerformanceSummary";
import WinRateChart from "../components/charts/WinRateChart";
import type { PerformanceStats } from "../api/performance";
import type { PortfolioStats } from "../api/portfolio";
import { ApiError } from "../api/client";
import { fetchPerformance } from "../api/performance";
import { fetchPortfolio } from "../api/portfolio";

function fmt(n: number, d = 2) {
  return Number(n).toFixed(d);
}

function pct(n: number) {
  return `${n >= 0 ? "+" : ""}${fmt(n, 2)}%`;
}

export default function Analytics() {
  const { t } = useTranslation(["analytics", "common"]);
  const [perf, setPerf] = useState<PerformanceStats | null>(null);
  const [port, setPort] = useState<PortfolioStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const [perfData, portData] = await Promise.all([
        fetchPerformance(),
        fetchPortfolio(),
      ]);
      setPerf(perfData);
      setPort(portData);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("page.loadError"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const hasTrades = port && port.total_trades > 0;
  const hasData = perf && hasTrades;

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
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={fetchAll} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            {t("common:retry")}
          </button>
        </div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("page.noData")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
          {t("page.sections.performanceMetrics")}
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <MetricCard label={t("page.metrics.sharpeRatio")} value={fmt(perf!.sharpe_ratio, 4)} />
          <MetricCard label={t("page.metrics.sortinoRatio")} value={fmt(perf!.sortino_ratio, 4)} />
          <MetricCard label={t("page.metrics.profitFactor")} value={fmt(perf!.profit_factor, 2)} />
          <MetricCard label={t("page.metrics.expectancy")} value={fmt(perf!.expectancy, 2)} />
          <MetricCard label={t("page.metrics.recoveryFactor")} value={fmt(perf!.recovery_factor, 2)} />
          <MetricCard label={t("page.metrics.calmarRatio")} value={fmt(perf!.calmar_ratio, 4)} />
          <MetricCard label={t("page.metrics.avgRMultiple")} value={fmt(perf!.average_r_multiple, 2)} />
          <MetricCard label={t("page.metrics.avgHoldHours")} value={fmt(perf!.average_holding_hours, 2)} />
          <MetricCard label={t("page.metrics.bestTrade")} value={fmt(perf!.best_trade, 2)} positive={perf!.best_trade > 0} />
          <MetricCard label={t("page.metrics.worstTrade")} value={fmt(perf!.worst_trade, 2)} positive={perf!.worst_trade > 0} />
          <MetricCard label={t("page.metrics.consecutiveWins")} value={String(perf!.consecutive_wins)} />
          <MetricCard label={t("page.metrics.consecutiveLosses")} value={String(perf!.consecutive_losses)} negative />
        </div>
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
          {t("page.sections.portfolioSummary")}
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <MetricCard label={t("page.portfolio.totalTrades")} value={String(port!.total_trades)} />
          <MetricCard label={t("page.portfolio.open")} value={String(port!.open_trades)} />
          <MetricCard label={t("page.portfolio.closed")} value={String(port!.closed_trades)} />
          <MetricCard label={t("page.portfolio.winRate")} value={pct(port!.win_rate)} />
          <MetricCard label={t("page.portfolio.lossRate")} value={pct(100 - port!.win_rate)} negative />
          <MetricCard label={t("page.portfolio.totalPnl")} value={`$${fmt(port!.total_pnl)}`} positive={port!.total_pnl > 0} negative={port!.total_pnl < 0} />
          <MetricCard label={t("page.portfolio.dailyPnl")} value={`$${fmt(port!.daily_pnl)}`} positive={port!.daily_pnl > 0} negative={port!.daily_pnl < 0} />
          <MetricCard label={t("page.portfolio.avgWin")} value={`$${fmt(port!.average_win)}`} positive />
          <MetricCard label={t("page.portfolio.avgLoss")} value={`$${fmt(port!.average_loss)}`} negative />
          <MetricCard
            label={t("page.portfolio.avgReturn")}
            value={`$${fmt(port!.closed_trades > 0 ? port!.total_pnl / port!.closed_trades : 0)}`}
            positive={port!.total_pnl > 0}
            negative={port!.total_pnl < 0}
          />
          <MetricCard label={t("page.portfolio.maxDrawdown")} value={pct(port!.max_drawdown)} negative />
          <MetricCard label={t("page.portfolio.openExposure")} value={`$${fmt(port!.current_open_exposure)}`} />
        </div>
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
          {t("page.sections.equityCurve")}
        </h2>
        <PerformanceChart
          equityCurve={port!.equity_curve.map((val, i) => ({
            time: String(i),
            value: val,
          }))}
        />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
          {t("page.sections.drawdown")}
        </h2>
        <DrawdownChart equityCurve={port!.equity_curve} />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
          {t("page.sections.winRate")}
        </h2>
        <WinRateChart winRate={port!.win_rate} totalTrades={port!.closed_trades} />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
          {t("page.sections.summary")}
        </h2>
        <PerformanceSummary
          totalTrades={port!.total_trades}
          winningTrades={port!.winning_trades}
          losingTrades={port!.losing_trades}
          winRate={port!.win_rate}
          totalPnl={port!.total_pnl}
          averageWin={port!.average_win}
          averageLoss={port!.average_loss}
          profitFactor={port!.profit_factor}
          maxDrawdown={port!.max_drawdown}
        />
      </section>
    </div>
  );
}



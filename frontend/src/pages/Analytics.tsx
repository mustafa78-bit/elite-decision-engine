import { useCallback, useEffect, useState } from "react";

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
      setError(e instanceof ApiError ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const hasTrades = port && port.total_trades > 0;
  const hasData = perf && hasTrades;

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading analytics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={fetchAll} className="ml-2 underline text-gray-400 hover:text-gray-200">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        No trade data yet — start trading to generate analytics
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Performance Metrics
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <MetricCard label="Sharpe Ratio" value={fmt(perf!.sharpe_ratio, 4)} />
          <MetricCard label="Sortino Ratio" value={fmt(perf!.sortino_ratio, 4)} />
          <MetricCard label="Profit Factor" value={fmt(perf!.profit_factor, 2)} />
          <MetricCard label="Expectancy" value={fmt(perf!.expectancy, 2)} />
          <MetricCard label="Recovery Factor" value={fmt(perf!.recovery_factor, 2)} />
          <MetricCard label="Calmar Ratio" value={fmt(perf!.calmar_ratio, 4)} />
          <MetricCard label="Avg R Multiple" value={fmt(perf!.average_r_multiple, 2)} />
          <MetricCard label="Avg Hold (hrs)" value={fmt(perf!.average_holding_hours, 2)} />
          <MetricCard label="Best Trade $" value={fmt(perf!.best_trade, 2)} positive={perf!.best_trade > 0} />
          <MetricCard label="Worst Trade $" value={fmt(perf!.worst_trade, 2)} positive={perf!.worst_trade > 0} />
          <MetricCard label="Consecutive Wins" value={String(perf!.consecutive_wins)} />
          <MetricCard label="Consecutive Losses" value={String(perf!.consecutive_losses)} negative />
        </div>
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Portfolio Summary
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <MetricCard label="Total Trades" value={String(port!.total_trades)} />
          <MetricCard label="Open" value={String(port!.open_trades)} />
          <MetricCard label="Closed" value={String(port!.closed_trades)} />
          <MetricCard label="Win Rate" value={pct(port!.win_rate)} />
          <MetricCard label="Loss Rate" value={pct(100 - port!.win_rate)} negative />
          <MetricCard label="Total PnL" value={`$${fmt(port!.total_pnl)}`} positive={port!.total_pnl > 0} negative={port!.total_pnl < 0} />
          <MetricCard label="Daily PnL" value={`$${fmt(port!.daily_pnl)}`} positive={port!.daily_pnl > 0} negative={port!.daily_pnl < 0} />
          <MetricCard label="Avg Win" value={`$${fmt(port!.average_win)}`} positive />
          <MetricCard label="Avg Loss" value={`$${fmt(port!.average_loss)}`} negative />
          <MetricCard
            label="Avg Return"
            value={`$${fmt(port!.closed_trades > 0 ? port!.total_pnl / port!.closed_trades : 0)}`}
            positive={port!.total_pnl > 0}
            negative={port!.total_pnl < 0}
          />
          <MetricCard label="Max Drawdown" value={pct(port!.max_drawdown)} negative />
          <MetricCard label="Open Exposure" value={`$${fmt(port!.current_open_exposure)}`} />
        </div>
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Equity Curve
        </h2>
        <PerformanceChart
          equityCurve={port!.equity_curve.map((val, i) => ({
            time: String(i),
            value: val,
          }))}
        />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Drawdown
        </h2>
        <DrawdownChart equityCurve={port!.equity_curve} />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Win Rate
        </h2>
        <WinRateChart winRate={port!.win_rate} totalTrades={port!.closed_trades} />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Summary
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



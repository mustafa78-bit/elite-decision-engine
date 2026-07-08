import { useEffect, useState } from "react";

interface PerformanceStats {
  sharpe_ratio: number;
  sortino_ratio: number;
  profit_factor: number;
  expectancy: number;
  recovery_factor: number;
  calmar_ratio: number;
  average_r_multiple: number;
  average_holding_hours: number;
  consecutive_wins: number;
  consecutive_losses: number;
  best_trade: number;
  worst_trade: number;
}

interface PortfolioStats {
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  daily_pnl: number;
  average_win: number;
  average_loss: number;
  profit_factor: number;
  max_drawdown: number;
  current_open_exposure: number;
  equity_curve: number[];
}

const API = "http://localhost:8000";

function fmt(n: number, d = 2) {
  return Number(n).toFixed(d);
}

function pct(n: number) {
  return `${n >= 0 ? "+" : ""}${fmt(n, 2)}%`;
}

export default function Analytics() {
  const [perf, setPerf] = useState<PerformanceStats | null>(null);
  const [port, setPort] = useState<PortfolioStats | null>(null);

  useEffect(() => {
    fetch(`${API}/performance`).then((r) => r.json()).then(setPerf);
    fetch(`${API}/portfolio`).then((r) => r.json()).then(setPort);
  }, []);

  return (
    <div className="space-y-6">
      {perf && (
        <section>
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
            Performance Metrics
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <MetricCard label="Sharpe Ratio" value={fmt(perf.sharpe_ratio, 4)} />
            <MetricCard label="Sortino Ratio" value={fmt(perf.sortino_ratio, 4)} />
            <MetricCard label="Profit Factor" value={fmt(perf.profit_factor, 2)} />
            <MetricCard label="Expectancy" value={fmt(perf.expectancy, 2)} />
            <MetricCard label="Recovery Factor" value={fmt(perf.recovery_factor, 2)} />
            <MetricCard label="Calmar Ratio" value={fmt(perf.calmar_ratio, 4)} />
            <MetricCard label="Avg R Multiple" value={fmt(perf.average_r_multiple, 2)} />
            <MetricCard label="Avg Hold (hrs)" value={fmt(perf.average_holding_hours, 2)} />
            <MetricCard label="Best Trade $" value={fmt(perf.best_trade, 2)} positive={perf.best_trade > 0} />
            <MetricCard label="Worst Trade $" value={fmt(perf.worst_trade, 2)} positive={perf.worst_trade > 0} />
            <MetricCard label="Consecutive Wins" value={String(perf.consecutive_wins)} />
            <MetricCard label="Consecutive Losses" value={String(perf.consecutive_losses)} negative />
          </div>
        </section>
      )}

      {port && (
        <>
          <section>
            <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
              Portfolio Summary
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <MetricCard label="Total Trades" value={String(port.total_trades)} />
              <MetricCard label="Open" value={String(port.open_trades)} />
              <MetricCard label="Closed" value={String(port.closed_trades)} />
              <MetricCard label="Win Rate" value={pct(port.win_rate)} />
              <MetricCard label="Total PnL" value={`$${fmt(port.total_pnl)}`} positive={port.total_pnl > 0} negative={port.total_pnl < 0} />
              <MetricCard label="Daily PnL" value={`$${fmt(port.daily_pnl)}`} positive={port.daily_pnl > 0} negative={port.daily_pnl < 0} />
              <MetricCard label="Avg Win" value={`$${fmt(port.average_win)}`} positive />
              <MetricCard label="Avg Loss" value={`$${fmt(port.average_loss)}`} negative />
              <MetricCard label="Max Drawdown" value={pct(port.max_drawdown)} negative />
              <MetricCard label="Open Exposure" value={`$${fmt(port.current_open_exposure)}`} />
            </div>
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
              Equity Curve
            </h2>
            <EquityCurve curve={port.equity_curve} />
          </section>
        </>
      )}

      {!perf && !port && (
        <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
          Loading analytics...
        </div>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  positive,
  negative,
}: {
  label: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
}) {
  const color = positive
    ? "text-green-400"
    : negative
      ? "text-red-400"
      : "text-gray-100";
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-sm font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function EquityCurve({ curve }: { curve: number[] }) {
  if (curve.length < 2) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Not enough data
      </div>
    );
  }

  const min = Math.min(...curve);
  const max = Math.max(...curve);
  const range = max - min || 1;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <div className="flex items-end gap-[2px] h-32">
        {curve.map((val, i) => {
          const h = ((val - min) / range) * 100;
          const color = val >= curve[i > 0 ? i - 1 : i] ? "bg-green-600" : "bg-red-600";
          return (
            <div
              key={i}
              className={`flex-1 ${color} rounded-t`}
              style={{ height: `${Math.max(h, 1)}%` }}
              title={`$${fmt(val, 2)}`}
            />
          );
        })}
      </div>
      <div className="flex justify-between text-[10px] text-gray-500 mt-1">
        <span>${fmt(min, 0)}</span>
        <span>$${fmt(max, 0)}</span>
      </div>
    </div>
  );
}

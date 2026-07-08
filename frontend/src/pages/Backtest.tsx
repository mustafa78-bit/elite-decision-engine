import { useCallback, useEffect, useState } from "react";

import type { BacktestResult } from "../api/backtest";
import { fetchBacktest } from "../api/backtest";
import { ApiError } from "../api/client";

export default function Backtest() {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchBacktest();
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load backtest");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Running backtest...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded mb-4">
        {error}
        <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">Retry</button>
      </div>
    );
  }

  if (!data) return null;

  const perf = data.performance;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">Backtest Report</h2>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard label="Total PnL" value={`${perf.total_pnl >= 0 ? "+" : ""}${perf.total_pnl.toFixed(2)}`} positive={perf.total_pnl >= 0} />
        <MetricCard label="ROI" value={`${perf.roi_pct.toFixed(1)}%`} positive={perf.roi_pct >= 0} />
        <MetricCard label="Win Rate" value={`${perf.win_rate_pct.toFixed(1)}%`} positive={perf.win_rate_pct >= 50} />
        <MetricCard label="Profit Factor" value={perf.profit_factor.toFixed(2)} positive={perf.profit_factor >= 1.5} />
        <MetricCard label="Avg Win" value={`+${perf.avg_win.toFixed(2)}`} positive />
        <MetricCard label="Avg Loss" value={`-${perf.avg_loss.toFixed(2)}`} positive={false} />
        <MetricCard label="Max Drawdown" value={perf.max_drawdown.toFixed(2)} positive={perf.max_drawdown < 500} />
        <MetricCard label="Sharpe" value={perf.sharpe_ratio.toFixed(4)} positive={perf.sharpe_ratio >= 1.0} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Total Signals</div>
          <div className="text-lg text-gray-200 tabular-nums">{data.summary.total_signals}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Approved</div>
          <div className="text-lg text-green-400 tabular-nums">{data.summary.approved_signals}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Rejected</div>
          <div className="text-lg text-red-400 tabular-nums">{data.summary.rejected_signals}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Approval Rate</div>
          <div className="text-lg text-gray-200 tabular-nums">{data.summary.approval_rate}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Total Trades</div>
          <div className="text-lg text-gray-200 tabular-nums">{data.trades.total}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Wins</div>
          <div className="text-lg text-green-400 tabular-nums">{data.trades.wins}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Losses</div>
          <div className="text-lg text-red-400 tabular-nums">{data.trades.losses}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-gray-500">Open / Closed</div>
          <div className="text-lg text-gray-200 tabular-nums">{data.trades.open} / {data.trades.closed}</div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, positive }: { label: string; value: string; positive: boolean }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <div className="text-[9px] uppercase tracking-wider text-gray-500">{label}</div>
      <div className={`text-lg tabular-nums ${positive ? "text-green-400" : "text-red-400"}`}>{value}</div>
    </div>
  );
}

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
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Running backtest...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded mb-4">
        {error}
        <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Retry</button>
      </div>
    );
  }

  if (!data) return null;

  const perf = data.performance;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Backtest Report</h2>

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
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Total Signals</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.summary.total_signals}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Approved</div>
          <div className="text-lg text-[var(--accent-green)] tabular-nums">{data.summary.approved_signals}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Rejected</div>
          <div className="text-lg text-[var(--accent-red)] tabular-nums">{data.summary.rejected_signals}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Approval Rate</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.summary.approval_rate}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Total Trades</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.trades.total}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Wins</div>
          <div className="text-lg text-[var(--accent-green)] tabular-nums">{data.trades.wins}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Losses</div>
          <div className="text-lg text-[var(--accent-red)] tabular-nums">{data.trades.losses}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">Open / Closed</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.trades.open} / {data.trades.closed}</div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, positive }: { label: string; value: string; positive: boolean }) {
  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
      <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{label}</div>
      <div className={`text-lg tabular-nums ${positive ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>{value}</div>
    </div>
  );
}

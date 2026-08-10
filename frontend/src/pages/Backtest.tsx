import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { BacktestResult } from "../api/backtest";
import { fetchBacktest } from "../api/backtest";
import { ApiError } from "../api/client";

export default function Backtest() {
  const { t } = useTranslation(["backtest", "common"]);
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
      setError(e instanceof ApiError ? e.message : t("backtest:page.loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("backtest:page.running")}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded mb-4">
        {error}
        <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">{t("common:retry")}</button>
      </div>
    );
  }

  if (!data) return null;

  const perf = data.performance;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">{t("backtest:page.title")}</h2>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricCard label={t("backtest:metrics.totalPnl")} value={`${perf.total_pnl >= 0 ? "+" : ""}${perf.total_pnl.toFixed(2)}`} positive={perf.total_pnl >= 0} />
        <MetricCard label={t("backtest:metrics.roi")} value={`${perf.roi_pct.toFixed(1)}%`} positive={perf.roi_pct >= 0} />
        <MetricCard label={t("backtest:metrics.winRate")} value={`${perf.win_rate_pct.toFixed(1)}%`} positive={perf.win_rate_pct >= 50} />
        <MetricCard label={t("backtest:metrics.profitFactor")} value={perf.profit_factor.toFixed(2)} positive={perf.profit_factor >= 1.5} />
        <MetricCard label={t("backtest:metrics.avgWin")} value={`+${perf.avg_win.toFixed(2)}`} positive />
        <MetricCard label={t("backtest:metrics.avgLoss")} value={`-${perf.avg_loss.toFixed(2)}`} positive={false} />
        <MetricCard label={t("backtest:metrics.maxDrawdown")} value={perf.max_drawdown.toFixed(2)} positive={perf.max_drawdown < 500} />
        <MetricCard label={t("backtest:metrics.sharpe")} value={perf.sharpe_ratio.toFixed(4)} positive={perf.sharpe_ratio >= 1.0} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:summary.totalSignals")}</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.summary.total_signals}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:summary.approved")}</div>
          <div className="text-lg text-[var(--accent-green)] tabular-nums">{data.summary.approved_signals}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:summary.rejected")}</div>
          <div className="text-lg text-[var(--accent-red)] tabular-nums">{data.summary.rejected_signals}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:summary.approvalRate")}</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.summary.approval_rate}%</div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:trades.total")}</div>
          <div className="text-lg text-[var(--text-primary)] tabular-nums">{data.trades.total}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:trades.wins")}</div>
          <div className="text-lg text-[var(--accent-green)] tabular-nums">{data.trades.wins}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:trades.losses")}</div>
          <div className="text-lg text-[var(--accent-red)] tabular-nums">{data.trades.losses}</div>
        </div>
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-3">
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)]">{t("backtest:trades.openClosed")}</div>
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

import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";

import RegimeBadge from "../components/market/RegimeBadge";
import type { LayoutContext } from "../components/layout/Layout";
import { apiFetch, ApiError } from "../api/client";

interface MarketData {
  symbol: string;
  price: number;
  regime: string;
  regime_score: number;
  rsi: number;
  atr: number;
  btc_health_score: number;
  error?: string;
}

interface RiskSummary {
  risk_score: number;
  open_trades: number;
  max_open_trades: number;
  daily_loss: number;
  max_daily_loss: number;
}

interface PerfSummary {
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  sharpe_ratio: number;
}

function OverviewCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-secondary)] mb-3">
        {label}
      </h3>
      {children}
    </div>
  );
}

export default function Overview() {
  const { openTrades, closedTrades } = useOutletContext<LayoutContext>();
  const [market, setMarket] = useState<MarketData | null>(null);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [perf, setPerf] = useState<PerfSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const [m, r, po] = await Promise.all([
        apiFetch<MarketData>("/market"),
        apiFetch<RiskSummary>("/risk"),
        apiFetch<PerfSummary>("/portfolio"),
      ]);
      if (m.error) {
        setError(m.error);
        return;
      }
      setMarket(m);
      setRisk(r);
      setPerf(po);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading overview...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/30 bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={fetchAll} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        Terminal Overview
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {market && (
          <OverviewCard label="BTC Status">
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg font-bold tabular-nums text-[var(--text-primary)]">
                ${market.price.toLocaleString(undefined, { minimumFractionDigits: 0 })}
              </span>
              <RegimeBadge regime={market.regime} />
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              <div><span className="text-[var(--text-secondary)]">RSI</span> <span className="tabular-nums text-[var(--text-primary)] float-right">{market.rsi.toFixed(0)}</span></div>
              <div><span className="text-[var(--text-secondary)]">Health</span> <span className="tabular-nums text-[var(--text-primary)] float-right">{(market.btc_health_score * 100).toFixed(0)}%</span></div>
            </div>
          </OverviewCard>
        )}

        <OverviewCard label="Trades">
          <div className="text-2xl font-bold tabular-nums text-[var(--text-primary)] mb-2">
            {openTrades.length}
            <span className="text-sm text-[var(--text-secondary)] ml-1">/ {openTrades.length + closedTrades.length}</span>
          </div>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <div><span className="text-[var(--accent-green)]">{openTrades.length} open</span></div>
            <div><span className="text-[var(--text-secondary)] tabular-nums float-right">{closedTrades.length} closed</span></div>
          </div>
        </OverviewCard>

        {risk && (
          <OverviewCard label="Risk">
            <div className="text-2xl font-bold tabular-nums mb-2">
              <span className={risk.risk_score >= 0.5 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                {(risk.risk_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              <div><span className="text-[var(--text-secondary)]">Open</span> <span className="tabular-nums text-[var(--text-primary)] float-right">{risk.open_trades}/{risk.max_open_trades}</span></div>
              <div><span className="text-[var(--text-secondary)]">Loss</span> <span className={`tabular-nums float-right ${risk.daily_loss < 0 ? "text-[var(--accent-red)]" : "text-[var(--text-primary)]"}`}>${Math.abs(risk.daily_loss).toFixed(0)}</span></div>
            </div>
          </OverviewCard>
        )}

        {perf && (
          <OverviewCard label="Performance">
            <div className={`text-2xl font-bold tabular-nums mb-2 ${totalPnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
              ${totalPnl.toFixed(0)}
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              <div><span className="text-[var(--text-secondary)]">Win Rate</span> <span className="tabular-nums text-[var(--text-primary)] float-right">{perf.win_rate.toFixed(0)}%</span></div>
              <div><span className="text-[var(--text-secondary)]">Sharpe</span> <span className="tabular-nums text-[var(--text-primary)] float-right">{perf.sharpe_ratio.toFixed(2)}</span></div>
            </div>
          </OverviewCard>
        )}
      </div>
    </div>
  );
}

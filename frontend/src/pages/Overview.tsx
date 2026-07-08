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
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
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
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading overview...
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

  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        Terminal Overview
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {market && (
          <OverviewCard label="BTC Status">
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg font-bold tabular-nums text-gray-100">
                ${market.price.toLocaleString(undefined, { minimumFractionDigits: 0 })}
              </span>
              <RegimeBadge regime={market.regime} />
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              <div><span className="text-gray-500">RSI</span> <span className="tabular-nums text-gray-200 float-right">{market.rsi.toFixed(0)}</span></div>
              <div><span className="text-gray-500">Health</span> <span className="tabular-nums text-gray-200 float-right">{(market.btc_health_score * 100).toFixed(0)}%</span></div>
            </div>
          </OverviewCard>
        )}

        <OverviewCard label="Trades">
          <div className="text-2xl font-bold tabular-nums text-gray-100 mb-2">
            {openTrades.length}
            <span className="text-sm text-gray-500 ml-1">/ {openTrades.length + closedTrades.length}</span>
          </div>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <div><span className="text-green-400">{openTrades.length} open</span></div>
            <div><span className="text-gray-500 tabular-nums float-right">{closedTrades.length} closed</span></div>
          </div>
        </OverviewCard>

        {risk && (
          <OverviewCard label="Risk">
            <div className="text-2xl font-bold tabular-nums mb-2">
              <span className={risk.risk_score >= 0.5 ? "text-green-400" : "text-red-400"}>
                {(risk.risk_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              <div><span className="text-gray-500">Open</span> <span className="tabular-nums text-gray-200 float-right">{risk.open_trades}/{risk.max_open_trades}</span></div>
              <div><span className="text-gray-500">Loss</span> <span className={`tabular-nums float-right ${risk.daily_loss < 0 ? "text-red-400" : "text-gray-200"}`}>${Math.abs(risk.daily_loss).toFixed(0)}</span></div>
            </div>
          </OverviewCard>
        )}

        {perf && (
          <OverviewCard label="Performance">
            <div className={`text-2xl font-bold tabular-nums mb-2 ${totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
              ${totalPnl.toFixed(0)}
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              <div><span className="text-gray-500">Win Rate</span> <span className="tabular-nums text-gray-200 float-right">{perf.win_rate.toFixed(0)}%</span></div>
              <div><span className="text-gray-500">Sharpe</span> <span className="tabular-nums text-gray-200 float-right">{perf.sharpe_ratio.toFixed(2)}</span></div>
            </div>
          </OverviewCard>
        )}
      </div>
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";

import type { TradingControlData } from "../api/trading_control";
import { fetchTradingControl } from "../api/trading_control";
import { ApiError } from "../api/client";

export default function TradingControl() {
  const [data, setData] = useState<TradingControlData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchTradingControl();
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load trading control data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading trading control...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-[var(--accent-red)] text-xs p-4 border border-red-900 bg-[var(--accent-red)]/10 rounded mb-4">
        {error}
        <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Retry</button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Trading Control Center</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] mb-3">Exchanges</h3>
          <div className="space-y-2">
            {data.exchanges.map((ex) => (
              <div key={ex.name} className="flex items-center justify-between text-xs">
                <span className="text-[var(--text-primary)]">{ex.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${ex.status === "connected" ? "bg-[var(--accent-green)]" : "bg-[var(--accent-red)]"}`} />
                  <span className={ex.trading_enabled ? "text-[var(--accent-green)]" : "text-[var(--accent-yellow)]"}>
                    {ex.trading_enabled ? "active" : "paper"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] mb-3">Signals</h3>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-[var(--text-secondary)] text-[9px]">Total</div>
              <div className="text-[var(--text-primary)] tabular-nums">{data.signals.total}</div>
            </div>
            <div>
              <div className="text-[var(--text-secondary)] text-[9px]">Open</div>
              <div className="text-[var(--accent-yellow)] tabular-nums">{data.signals.open}</div>
            </div>
            <div>
              <div className="text-[var(--text-secondary)] text-[9px]">Approved</div>
              <div className="text-[var(--accent-green)] tabular-nums">{data.signals.approved}</div>
            </div>
          </div>
        </div>

        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] mb-3">Trades</h3>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-[var(--text-secondary)] text-[9px]">Total</div>
              <div className="text-[var(--text-primary)] tabular-nums">{data.trades.total}</div>
            </div>
            <div>
              <div className="text-[var(--text-secondary)] text-[9px]">Open</div>
              <div className="text-[var(--accent-blue)] tabular-nums">{data.trades.open}</div>
            </div>
            <div>
              <div className="text-[var(--text-secondary)] text-[9px]">Closed</div>
              <div className="text-[var(--text-secondary)] tabular-nums">{data.trades.closed}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] mb-3">Shadow Trading</h3>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-[var(--text-secondary)]">Mode</span>
              <span className="text-[var(--accent-green)]">{data.shadow.mode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--text-secondary)]">Engine</span>
              <span className="text-[var(--text-primary)]">{data.shadow.engine}</span>
            </div>
          </div>
        </div>

        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] mb-3">Risk Limits</h3>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-[var(--text-secondary)]">Max Open Trades</span>
              <span className="text-[var(--text-primary)] tabular-nums">{data.risk.max_open_trades}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--text-secondary)]">Max Daily Loss</span>
              <span className="text-[var(--text-primary)] tabular-nums">${data.risk.max_daily_loss.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

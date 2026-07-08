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
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading trading control...
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

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">Trading Control Center</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Exchanges</h3>
          <div className="space-y-2">
            {data.exchanges.map((ex) => (
              <div key={ex.name} className="flex items-center justify-between text-xs">
                <span className="text-gray-300">{ex.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${ex.status === "connected" ? "bg-green-400" : "bg-red-400"}`} />
                  <span className={ex.trading_enabled ? "text-green-400" : "text-yellow-400"}>
                    {ex.trading_enabled ? "active" : "paper"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Signals</h3>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-gray-500 text-[9px]">Total</div>
              <div className="text-gray-200 tabular-nums">{data.signals.total}</div>
            </div>
            <div>
              <div className="text-gray-500 text-[9px]">Open</div>
              <div className="text-yellow-400 tabular-nums">{data.signals.open}</div>
            </div>
            <div>
              <div className="text-gray-500 text-[9px]">Approved</div>
              <div className="text-green-400 tabular-nums">{data.signals.approved}</div>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Trades</h3>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-gray-500 text-[9px]">Total</div>
              <div className="text-gray-200 tabular-nums">{data.trades.total}</div>
            </div>
            <div>
              <div className="text-gray-500 text-[9px]">Open</div>
              <div className="text-blue-400 tabular-nums">{data.trades.open}</div>
            </div>
            <div>
              <div className="text-gray-500 text-[9px]">Closed</div>
              <div className="text-gray-400 tabular-nums">{data.trades.closed}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Shadow Trading</h3>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-500">Mode</span>
              <span className="text-green-400">{data.shadow.mode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Engine</span>
              <span className="text-gray-300">{data.shadow.engine}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded p-4">
          <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Risk Limits</h3>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-500">Max Open Trades</span>
              <span className="text-gray-300 tabular-nums">{data.risk.max_open_trades}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Max Daily Loss</span>
              <span className="text-gray-300 tabular-nums">${data.risk.max_daily_loss.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

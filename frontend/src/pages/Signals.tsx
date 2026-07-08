import { useCallback, useEffect, useState } from "react";

import LiveSignalTable from "../components/signals/LiveSignalTable";
import SignalScoreCard from "../components/signals/SignalScoreCard";
import SignalTimeline from "../components/signals/SignalTimeline";
import type { SignalRow } from "../api/signals";
import { ApiError } from "../api/client";
import { fetchSignals } from "../api/signals";

export default function Signals() {
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [selected, setSelected] = useState<SignalRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSignals = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchSignals();
      setSignals(data);
      if (data.length > 0 && !selected) {
        setSelected(data[0]);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load signals");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSignals(); }, [loadSignals]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading signals...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={loadSignals} className="ml-2 underline text-gray-400 hover:text-gray-200">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-gray-500">
          Live Signals ({signals.length})
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <LiveSignalTable signals={signals} />

          {selected && (
            <div className="lg:hidden">
              <SignalScoreCard
                symbol={selected.symbol}
                side={selected.side}
                confidence={selected.confidence}
                decision={selected.decision}
                finalScore={selected.final_score}
                trendScore={selected.trend_score}
                volumeScore={selected.volume_score}
                btcScore={selected.btc_score}
                riskScore={selected.risk_score}
              />
            </div>
          )}
        </div>

        <div className="lg:col-span-1 space-y-4">
          {selected && (
            <div className="hidden lg:block">
              <SignalScoreCard
                symbol={selected.symbol}
                side={selected.side}
                confidence={selected.confidence}
                decision={selected.decision}
                finalScore={selected.final_score}
                trendScore={selected.trend_score}
                volumeScore={selected.volume_score}
                btcScore={selected.btc_score}
                riskScore={selected.risk_score}
              />
            </div>
          )}

          <SignalTimeline signals={signals} />
        </div>
      </div>
    </div>
  );
}

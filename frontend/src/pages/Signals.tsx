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
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading signals...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)] bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={loadSignals} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
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

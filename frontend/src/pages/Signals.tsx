import { useCallback, useEffect, useState } from "react";

import LiveSignalTable from "../components/signals/LiveSignalTable";
import SignalScoreCard from "../components/signals/SignalScoreCard";
import SignalTimeline from "../components/signals/SignalTimeline";
import type { SignalRow } from "../api/signals";
import { ApiError } from "../api/client";
import { fetchSignals } from "../api/signals";
import { PageHeader } from "../components/ui/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";

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
      <div className="space-y-4">
        <PageHeader
          title="Live Signals"
          subtitle="Tick-by-tick consensus-driven trading signal feed"
        />
        <EmptyState
          loading
          title="Loading signals..."
          description="Fetching tick-by-tick consensus signals from the multi-agent decision engine."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Live Signals"
          subtitle="Tick-by-tick consensus-driven trading signal feed"
        />
        <EmptyState
          title="No signal data available"
          description="The consensus-driven trading signal service is currently offline or loading. Reconnect or try again shortly."
          error={error}
          actionButton={{
            label: "Retry connection",
            onClick: loadSignals,
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Live Signals"
        subtitle={`Tick-by-tick consensus-driven trading signal feed (Active: ${signals.length})`}
      />

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

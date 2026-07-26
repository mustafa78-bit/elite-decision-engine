import { useCallback, useEffect, useState } from "react";

import LiveSignalTable from "../components/signals/LiveSignalTable";
import SignalScoreCard from "../components/signals/SignalScoreCard";
import SignalTimeline from "../components/signals/SignalTimeline";
import type { SignalRow } from "../api/signals";
import { ApiError } from "../api/client";
import { fetchSignals } from "../api/signals";
import { LoadingScreen } from "../components/layout/LoadingScreen";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader, PageContainer } from "../components/ui/PageHeader";

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
      <PageContainer>
        <PageHeader title="Signals" subtitle="Live Signals Feed & Sentiment Insights" />
        <LoadingScreen variant="table" />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <PageHeader title="Signals" subtitle="Live Signals Feed & Sentiment Insights" />
        <ErrorState message={error} onRetry={loadSignals} />
      </PageContainer>
    );
  }

  if (signals.length === 0) {
    return (
      <PageContainer>
        <PageHeader title="Signals" subtitle="Live Signals Feed & Sentiment Insights" />
        <EmptyState
          title="No Signals Generated"
          description="The AI model queue has not generated any tactical entry or exit signals yet."
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader title="Signals" subtitle={`Live Signals Feed & Sentiment Insights (${signals.length})`} />

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
    </PageContainer>
  );
}

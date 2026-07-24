import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchSignalsRanking } from "../../api/signals_ranking";

export default function BestOpportunityCard() {
  const { data: ranked, loading, error, refetch } = useApi(() => fetchSignalsRanking(10), []);

  const best = (ranked || []).filter((s) => s.status === "OPEN")[0];

  return (
    <Card>
      <CardContent className="p-3">
        <p className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Best Opportunity</p>

        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-5 w-20" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <p className="text-[12px] text-[var(--accent-red)] font-mono">Failed to load</p>
            <Button variant="ghost" size="sm" onClick={refetch}>Retry</Button>
          </div>
        ) : !best ? (
          <p className="text-[12px] text-[var(--text-muted)] font-mono text-center py-3">No opportunity right now</p>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className={best.side === "LONG" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                {best.side === "LONG" ? "▲" : "▼"}
              </span>
              <span className="text-sm font-semibold text-[var(--text-primary)]">{best.symbol}</span>
              <span className="text-[12px] font-mono text-[var(--text-muted)] ml-auto">
                Score {best.score.toFixed(1)}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[12px] font-mono">
              <span className="text-[var(--text-muted)]">Confidence</span>
              <span className="text-[var(--text-primary)] text-right">{(best.confidence * 100).toFixed(0)}%</span>
              <span className="text-[var(--text-muted)]">Trend</span>
              <span className="text-[var(--text-primary)] text-right">{best.trend_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">Volume</span>
              <span className="text-[var(--text-primary)] text-right">{best.volume_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">Risk Adj</span>
              <span className="text-[var(--text-primary)] text-right">{best.risk_score.toFixed(1)}</span>
            </div>

            <div className="flex items-center justify-between pt-1 border-t border-[var(--border-subtle)]">
              <span className="text-[12px] font-mono uppercase text-[var(--accent-green)]">{best.decision}</span>
              <span className="text-[12px] font-mono text-[var(--text-muted)]">{best.timeframe}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

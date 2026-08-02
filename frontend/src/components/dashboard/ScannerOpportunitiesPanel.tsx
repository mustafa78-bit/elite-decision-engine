import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchScannerDashboard, type ScannerOpportunity } from "../../api/scanner";
import { catalystIcon, shortLabel } from "./MarketCatalystCard";

function OpportunityRow({ opp }: { opp: ScannerOpportunity }) {
  const isLong = opp.side === "LONG";
  const sideColor = isLong ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]";

  return (
    <div className="py-1.5 border-b border-[var(--border-subtle)] last:border-0">
      <div className="flex items-center gap-2">
        <span className="text-[9px] font-mono text-[var(--text-muted)] w-4">#{opp.rank}</span>
        <span className={sideColor}>{isLong ? "▲" : "▼"}</span>
        <span className="text-xs font-semibold text-[var(--text-primary)]">{opp.symbol}</span>
        <span className="text-[9px] font-mono text-[var(--text-muted)] ml-auto">
          {opp.price != null ? `$${opp.price.toLocaleString()}` : "—"}
        </span>
      </div>

      <div className="flex items-center justify-between mt-0.5">
        <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase">{opp.strategy}</span>
        <span className="text-[9px] font-mono text-[var(--text-muted)]">
          {`Score ${opp.score.toFixed(1)}`}
        </span>
        <span className="text-[9px] font-mono text-[var(--text-primary)]">
          {`${(opp.confidence * 100).toFixed(0)}%`}
        </span>
      </div>

      {opp.signals.length > 0 && (
        <div className="flex items-center gap-1.5 mt-1">
          {opp.signals.slice(0, 3).map((s) => (
            <span
              key={s}
              className="text-[8px] font-mono text-[var(--text-muted)] flex items-center gap-0.5"
              title={s}
            >
              <span>{catalystIcon(s)}</span>
              <span>{shortLabel(s)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ScannerOpportunitiesPanel() {
  const { data: dash, loading, error, refetch } = useApi(() => fetchScannerDashboard(8), []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ranked Opportunities</CardTitle>
        {dash && (
          <span className="text-[10px] font-mono text-[var(--text-muted)]">
            {dash.opportunities_found} found
          </span>
        )}
      </CardHeader>
      <CardContent className="max-h-80 overflow-y-auto">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <p className="text-[10px] text-[var(--accent-red)] font-mono">Failed to load</p>
            <Button variant="ghost" size="sm" onClick={refetch}>Retry</Button>
          </div>
        ) : !dash || dash.top_opportunities.length === 0 ? (
          <p className="text-[10px] text-[var(--text-muted)] font-mono text-center py-3">
            No opportunities found
          </p>
        ) : (
          <div>
            {dash.top_opportunities.map((opp) => (
              <OpportunityRow key={`${opp.symbol}-${opp.side}-${opp.rank}`} opp={opp} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

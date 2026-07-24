import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchRegime } from "../../api/regime";
import { fetchMarket } from "../../api/market";

function buildBrief(data: { regime: string; trend: string; btcHealth: number; rsi: number; volatilityState: string }): string[] {
  const lines: string[] = [];
  if (data.regime) lines.push(`Regime: ${data.regime}`);
  if (data.trend) lines.push(`Trend: ${data.trend}`);
  if (data.rsi) lines.push(`RSI: ${data.rsi.toFixed(0)}`);
  if (data.volatilityState) lines.push(`Volatility: ${data.volatilityState}`);
  if (lines.length === 0) lines.push("Awaiting market data...");
  return lines;
}

export default function FounderMorningBrief() {
  const { data: regime, loading, error, refetch } = useApi(fetchRegime, []);
  const { data: market } = useApi(fetchMarket, []);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-3">
          <div className="h-3 w-24 bg-[var(--bg-elevated)] rounded animate-pulse mb-3" />
          <div className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-3 w-5/6" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col items-center gap-3 py-2">
            <p className="text-[13px] text-[var(--accent-red)] font-mono">Failed to load morning brief</p>
            <Button variant="ghost" size="sm" onClick={refetch}>Retry</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const lines = buildBrief({
    regime: regime?.regime || "UNKNOWN",
    trend: regime?.trend || "NEUTRAL",
    btcHealth: regime?.btc_health ?? 0.5,
    rsi: market?.rsi ?? regime?.rsi ?? 50,
    volatilityState: regime?.volatility_state || "NORMAL",
  });

  return (
    <Card>
      <CardContent className="p-3">
        <p className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Morning Brief</p>
        <div className="space-y-1">
          {lines.map((line, i) => (
            <p key={i} className="text-[13px] text-[var(--text-secondary)] leading-relaxed">{line}</p>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

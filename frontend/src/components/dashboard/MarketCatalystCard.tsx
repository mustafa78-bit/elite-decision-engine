import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchScannerDashboard } from "../../api/scanner";

const CATALYST_ICONS: Record<string, string> = {
  PRICE_BREAKOUT_HIGH: "🚀",
  PRICE_BREAKOUT_LOW: "📉",
  HIGH_VOLUME_CONFIRMATION: "📊",
  EMA_CROSSOVER: "⚡",
  BULLISH_TREND_ALIGNED: "📈",
  BEARISH_TREND_ALIGNED: "📉",
  RSI_BULLISH: "💪",
  RSI_BEARISH: "⚠️",
  RSI_OVERBOUGHT: "🔄",
  RSI_OVERSOLD: "💫",
  MOMENTUM_STRONG: "🔥",
  OVERSOLD_REVERSAL: "↗️",
  OVERBOUGHT_REVERSAL: "↘️",
  HIGH_LIQUIDITY: "💧",
  LOW_LIQUIDITY: "🔴",
  HIGH_VOLUME: "📊",
};

function catalystIcon(signal: string): string {
  for (const [key, icon] of Object.entries(CATALYST_ICONS)) {
    if (signal.includes(key.replace(/_/g, "")) || signal === key) return icon;
  }
  return "◆";
}

function shortLabel(signal: string): string {
  return signal
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .slice(0, 28);
}

export default function MarketCatalystCard() {
  const { data: dash, loading, error, refetch } = useApi(() => fetchScannerDashboard(3), []);

  return (
    <Card>
      <CardContent className="p-3">
        <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Market Catalysts</p>

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
        ) : !dash || (dash.top_signals.length === 0 && dash.top_opportunities.length === 0) ? (
          <p className="text-[10px] text-[var(--text-muted)] font-mono text-center py-3">No catalyst signals detected</p>
        ) : (
          <div className="space-y-1">
            {dash.top_signals.slice(0, 4).map((s) => (
              <div key={s} className="flex items-center gap-2 text-[10px] font-mono py-1 border-b border-[var(--border-subtle)] last:border-0">
                <span className="text-[11px]">{catalystIcon(s)}</span>
                <span className="text-[var(--text-primary)]">{shortLabel(s)}</span>
              </div>
            ))}

            {dash.top_signals.length === 0 && dash.top_opportunities.length > 0 && (
              <div className="text-[10px] text-[var(--text-muted)] font-mono text-center py-1">
                {dash.opportunities_found} opportunities found • {dash.symbols_scanned} symbols scanned
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

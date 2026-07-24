import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { useApi } from "../../hooks/useApi";
import { fetchRegime } from "../../api/regime";
import { fetchMarket } from "../../api/market";

function SkeletonCard() {
  return (
    <Card>
      <CardContent className="p-3">
        <div className="h-3 w-16 bg-[var(--bg-elevated)] rounded animate-pulse mb-2" />
        <div className="h-5 w-20 bg-[var(--bg-elevated)] rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <Card>
      <CardContent className="p-3">
        <p className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-1">{label}</p>
        <p className={`text-sm font-semibold font-mono tabular-nums ${color || "text-[var(--text-primary)]"}`}>{value}</p>
      </CardContent>
    </Card>
  );
}

export default function FounderMarketSummary() {
  const { data: regime, loading: regimeLoading, error: regimeError, refetch: refetchRegime } = useApi(fetchRegime, []);
  const { data: market, loading: marketLoading, error: marketError, refetch: refetchMarket } = useApi(fetchMarket, []);

  if (regimeLoading || marketLoading) {
    return (
      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">Market Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </section>
    );
  }

  if (regimeError || marketError) {
    return (
      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">Market Summary</h2>
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col items-center gap-3 py-2">
              <p className="text-xs text-[var(--accent-red)] font-mono">Failed to load market data</p>
              <Button variant="ghost" size="sm" onClick={() => { refetchRegime(); refetchMarket(); }}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </section>
    );
  }

  const trendColor = regime?.trend === "BULLISH" ? "text-[var(--accent-green)]" :
    regime?.trend === "BEARISH" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]";

  const btcHealthPct = regime ? `${(regime.btc_health * 100).toFixed(0)}%` : "--";
  const btcHealthColor = regime && regime.btc_health > 0.6 ? "text-[var(--accent-green)]" :
    regime && regime.btc_health > 0.3 ? "text-[var(--accent-yellow)]" : "text-[var(--accent-red)]";

  return (
    <section>
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">Market Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard label="Market" value={regime?.regime || "--"} color={trendColor} />
        <StatCard label="Trend" value={regime?.trend || "--"} color={trendColor} />
        <StatCard label="BTC Health" value={btcHealthPct} color={btcHealthColor} />
        <StatCard label="Volatility" value={regime?.volatility_state || "--"} />
        <StatCard
          label="BTC Price"
          value={market?.price ? `$${market.price.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "--"}
        />
        <StatCard label="RSI" value={regime ? regime.rsi.toFixed(0) : "--"} />
      </div>
    </section>
  );
}

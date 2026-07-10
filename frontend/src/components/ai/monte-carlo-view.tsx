import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface MonteCarloResult {
  percentile: string;
  value: number;
  prob: number;
}

interface MonteCarloViewProps {
  symbol?: string;
  results?: MonteCarloResult[];
  expectedReturn?: number;
  riskOfRuin?: number;
}

export function MonteCarloView({
  symbol = "BTC/USDT",
  expectedReturn = 12.4,
  riskOfRuin = 3.2,
  results = [
    { percentile: "5% (Worst)", value: -18.5, prob: 5 },
    { percentile: "25%", value: -4.2, prob: 20 },
    { percentile: "50% (Median)", value: 11.8, prob: 50 },
    { percentile: "75%", value: 28.5, prob: 20 },
    { percentile: "95% (Best)", value: 45.2, prob: 5 },
  ],
}: MonteCarloViewProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Monte Carlo Simulation</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol} · 10,000 iterations</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-center">
            <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase">Expected Return</div>
            <div className="text-sm font-mono font-bold text-[var(--accent-green)] tabular-nums">+{expectedReturn.toFixed(1)}%</div>
          </div>
          <div className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-center">
            <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase">Risk of Ruin</div>
            <div className="text-sm font-mono font-bold text-[var(--accent-red)] tabular-nums">{riskOfRuin.toFixed(1)}%</div>
          </div>
        </div>
        <div className="relative h-24 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] overflow-hidden p-2">
          <div className="flex items-end h-full gap-1">
            {results.map((r) => (
              <div key={r.percentile} className="flex-1 flex flex-col items-center justify-end h-full">
                <div
                  className={`w-full rounded-t-sm ${r.value >= 0 ? "bg-[var(--accent-green)]/40" : "bg-[var(--accent-red)]/40"}`}
                  style={{ height: `${Math.min(Math.abs(r.value) * 2, 100)}%` }}
                />
              </div>
            ))}
          </div>
        </div>
        {results.map((r) => (
          <div key={r.percentile} className="flex items-center justify-between px-2 py-1 text-[10px] font-mono">
            <span className="text-[var(--text-secondary)]">{r.percentile}</span>
            <div className="flex items-center gap-2">
              <span className={`tabular-nums ${r.value >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                {r.value >= 0 ? "+" : ""}{r.value.toFixed(1)}%
              </span>
              <Badge variant="default" className="text-[8px]">{r.prob}% prob</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

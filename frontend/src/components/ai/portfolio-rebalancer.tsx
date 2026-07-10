import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

interface Allocation {
  symbol: string;
  current: number;
  target: number;
  diff: number;
}

interface PortfolioRebalancerProps {
  allocations?: Allocation[];
}

export function PortfolioRebalancer({
  allocations = [
    { symbol: "BTC/USDT", current: 45, target: 40, diff: 5 },
    { symbol: "ETH/USDT", current: 25, target: 30, diff: -5 },
    { symbol: "SOL/USDT", current: 15, target: 15, diff: 0 },
    { symbol: "AVAX/USDT", current: 10, target: 10, diff: 0 },
    { symbol: "LINK/USDT", current: 5, target: 5, diff: 0 },
  ],
}: PortfolioRebalancerProps) {
  const hasRebalance = allocations.some((a) => Math.abs(a.diff) > 2);

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Portfolio Rebalancer</CardTitle>
          {hasRebalance && <Badge variant="warning">Rebalance Needed</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {allocations.map((a) => (
          <div key={a.symbol}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[10px] font-mono text-[var(--text-secondary)]">{a.symbol}</span>
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-mono text-[var(--text-muted)]">C:{a.current}%</span>
                <span className="text-[9px] font-mono text-[var(--text-muted)]">T:{a.target}%</span>
                <span className={`text-[9px] font-mono tabular-nums ${a.diff > 0 ? "text-[var(--accent-red)]" : a.diff < 0 ? "text-[var(--accent-green)]" : "text-[var(--text-muted)]"}`}>
                  {a.diff > 0 ? "+" : ""}{a.diff}%
                </span>
              </div>
            </div>
            <div className="flex gap-0.5 h-1.5 rounded-full overflow-hidden bg-[var(--bg-base)]">
              <div className="bg-[var(--accent-blue)]" style={{ width: `${Math.min(a.current, a.target)}%` }} />
              {Math.abs(a.diff) > 0 && (
                <div className={`${a.diff > 0 ? "bg-[var(--accent-red)]/50" : "bg-[var(--accent-green)]/50"}`} style={{ width: `${Math.abs(a.diff)}%` }} />
              )}
            </div>
          </div>
        ))}
        {hasRebalance && (
          <Button variant="primary" className="w-full h-7 text-[10px] mt-2">Execute Rebalance</Button>
        )}
      </CardContent>
    </Card>
  );
}

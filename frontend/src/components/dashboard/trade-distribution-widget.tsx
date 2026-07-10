import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface TradeDistributionWidgetProps {
  wins?: number;
  losses?: number;
  total?: number;
  avgWin?: number;
  avgLoss?: number;
  largestWin?: number;
  largestLoss?: number;
}

export function TradeDistributionWidget({
  wins = 0,
  losses = 0,
  total = 0,
  avgWin = 0,
  avgLoss = 0,
  largestWin = 0,
  largestLoss = 0,
}: TradeDistributionWidgetProps) {
  const winRate = total > 0 ? (wins / total) * 100 : 0;
  const winPct = total > 0 ? (wins / total) * 100 : 0;
  const lossPct = total > 0 ? (losses / total) * 100 : 0;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Trade Distribution</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {total} total trades
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex h-3 rounded-full overflow-hidden">
          <div
            className="bg-[var(--accent-green)] transition-all"
            style={{ width: `${winPct}%` }}
          />
          <div
            className="bg-[var(--accent-red)] transition-all"
            style={{ width: `${lossPct}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] font-mono">
          <div className="text-center">
            <div className="text-[var(--accent-green)] font-medium">{wins}</div>
            <div className="text-[var(--text-muted)]">Wins</div>
            <div className="text-[var(--accent-green)]">{winRate.toFixed(0)}%</div>
          </div>
          <div className="text-center">
            <div className="text-[var(--accent-red)] font-medium">{losses}</div>
            <div className="text-[var(--text-muted)]">Losses</div>
            <div className="text-[var(--accent-red)]">{(100 - winRate).toFixed(0)}%</div>
          </div>
          <div className="text-center">
            <div className="text-[var(--text-primary)] font-medium">{avgWin.toFixed(0)}</div>
            <div className="text-[var(--text-muted)]">Avg Win</div>
            <div className="text-[var(--text-muted)]">$</div>
          </div>
          <div className="text-center">
            <div className="text-[var(--text-primary)] font-medium">{Math.abs(avgLoss).toFixed(0)}</div>
            <div className="text-[var(--text-muted)]">Avg Loss</div>
            <div className="text-[var(--text-muted)]">$</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

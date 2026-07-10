import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface Position {
  symbol: string;
  side: "long" | "short";
  size: number;
  entryPrice: number;
  markPrice: number;
  pnl: number;
  pnlPct: number;
}

interface PositionTrackerProps {
  positions?: Position[];
}

export function PositionTracker({ positions = [] }: PositionTrackerProps) {
  if (positions.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Positions</CardTitle></CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No open positions</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Positions ({positions.length})</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-3 py-1 border-b border-[var(--border-subtle)] flex text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          <span className="flex-[2]">Symbol</span>
          <span className="flex-[1] text-right">Size</span>
          <span className="flex-[2] text-right">Entry</span>
          <span className="flex-[2] text-right">Mark</span>
          <span className="flex-[2] text-right">PnL</span>
        </div>
        {positions.map((p) => (
          <div key={p.symbol} className="flex items-center px-3 py-1.5 text-[10px] font-mono border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
            <div className="flex-[2] flex items-center gap-1.5">
              <Badge variant={p.side === "long" ? "success" : "danger"} className="text-[8px] px-1 py-0">
                {p.side === "long" ? "L" : "S"}
              </Badge>
              <span className="text-[var(--text-secondary)]">{p.symbol}</span>
            </div>
            <span className="flex-[1] text-right text-[var(--text-primary)] tabular-nums">{p.size}</span>
            <span className="flex-[2] text-right text-[var(--text-muted)] tabular-nums">${p.entryPrice.toFixed(1)}</span>
            <span className="flex-[2] text-right text-[var(--text-muted)] tabular-nums">${p.markPrice.toFixed(1)}</span>
            <span className={`flex-[2] text-right tabular-nums ${p.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
              {p.pnl >= 0 ? "+" : ""}${p.pnl.toFixed(2)} ({p.pnlPct >= 0 ? "+" : ""}{p.pnlPct.toFixed(2)}%)
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

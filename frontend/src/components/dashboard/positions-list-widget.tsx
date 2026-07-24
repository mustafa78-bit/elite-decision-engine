import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { formatUSD } from "../../lib/utils";

interface PositionItem {
  symbol: string;
  side: "LONG" | "SHORT";
  size: number;
  entry: number;
  mark: number;
  pnl: number;
  pnlPct: number;
}

interface PositionsListWidgetProps {
  positions?: PositionItem[];
}

export function PositionsListWidget({ positions = [] }: PositionsListWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Positions</CardTitle>
        <span className="text-[12px] font-mono text-[var(--text-muted)]">
          {positions.length} active
        </span>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No open positions
          </div>
        ) : (
          <div className="space-y-1">
            <div className="grid grid-cols-5 gap-1 text-[12px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1 pb-1">
              <span>Symbol</span>
              <span>Side</span>
              <span className="text-right">Size</span>
              <span className="text-right">Entry</span>
              <span className="text-right">PnL</span>
            </div>
            {positions.map((p, i) => (
              <div key={p.symbol}>
                <div className="grid grid-cols-5 gap-1 items-center px-1 py-1.5 rounded-lg hover:bg-[var(--bg-elevated)]/50 transition-colors">
                  <span className="text-[13px] font-mono font-medium text-[var(--text-primary)]">
                    {p.symbol}
                  </span>
                  <Badge variant={p.side === "LONG" ? "success" : "danger"}>
                    {p.side}
                  </Badge>
                  <span className="text-[12px] font-mono tabular-nums text-right text-[var(--text-secondary)]">
                    {p.size}
                  </span>
                  <span className="text-[12px] font-mono tabular-nums text-right text-[var(--text-secondary)]">
                    {formatUSD(p.entry)}
                  </span>
                  <span
                    className={`text-[12px] font-mono tabular-nums text-right ${
                      p.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                    }`}
                  >
                    {p.pnl >= 0 ? "+" : ""}
                    {formatUSD(p.pnl)}
                  </span>
                </div>
                {i < positions.length - 1 && <Separator className="my-0.5" />}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

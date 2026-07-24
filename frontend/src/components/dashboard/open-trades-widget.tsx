import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { formatUSD } from "../../lib/utils";

interface TradeItem {
  symbol: string;
  side: string;
  size: number;
  entry_price: number;
  current_price: number;
  pnl: number;
}

interface OpenTradesWidgetProps {
  trades?: TradeItem[];
}

export function OpenTradesWidget({ trades = [] }: OpenTradesWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Open Trades</CardTitle>
        <span className="text-[12px] font-mono text-[var(--text-muted)]">
          {trades.length} positions
        </span>
      </CardHeader>
      <CardContent>
        {trades.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No open trades
          </div>
        ) : (
          <div className="space-y-1">
            {trades.slice(0, 5).map((t, i) => (
              <div key={`${t.symbol}-${i}`}>
                <div className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-medium text-[var(--text-primary)]">
                      {t.symbol}
                    </span>
                    <Badge
                      variant={
                        t.side === "LONG" || t.side === "BUY"
                          ? "success"
                          : "danger"
                      }
                    >
                      {t.side}
                    </Badge>
                  </div>
                  <div
                    className={`text-xs font-mono tabular-nums ${
                      t.pnl >= 0
                        ? "text-[var(--accent-green)]"
                        : "text-[var(--accent-red)]"
                    }`}
                  >
                    {t.pnl >= 0 ? "+" : ""}
                    {formatUSD(t.pnl)}
                  </div>
                </div>
                <div className="flex justify-between text-[12px] font-mono text-[var(--text-muted)]">
                  <span>
                    {t.size} @ {formatUSD(t.entry_price)}
                  </span>
                  <span>
                    {t.current_price > t.entry_price ? "+" : ""}
                    {(((t.current_price - t.entry_price) / t.entry_price) * 100).toFixed(1)}%
                  </span>
                </div>
                {i < trades.length - 1 && i < 4 && (
                  <Separator className="my-0.5" />
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

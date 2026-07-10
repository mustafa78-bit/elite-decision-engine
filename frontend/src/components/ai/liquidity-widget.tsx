import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";
import { Badge } from "../ui/badge";

interface LiquidityLevel {
  price: number;
  bidLiquidity: number;
  askLiquidity: number;
  ratio: number;
}

interface LiquidityWidgetProps {
  symbol?: string;
  levels?: LiquidityLevel[];
  overallScore?: number;
}

export function LiquidityWidget({
  symbol = "BTC/USDT",
  levels = [
    { price: 42500, bidLiquidity: 125, askLiquidity: 80, ratio: 1.56 },
    { price: 42000, bidLiquidity: 200, askLiquidity: 150, ratio: 1.33 },
    { price: 41500, bidLiquidity: 90, askLiquidity: 220, ratio: 0.41 },
  ],
  overallScore = 72,
}: LiquidityWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Liquidity Analysis</CardTitle>
          <Badge variant={overallScore > 70 ? "success" : overallScore > 40 ? "warning" : "danger"}>
            Score: {overallScore}
          </Badge>
        </div>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {symbol}
        </span>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {levels.map((l) => (
            <div key={l.price}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                  @ ${l.price.toLocaleString()}
                </span>
                <span className="text-[10px] font-mono tabular-nums text-[var(--text-muted)]">
                  Ratio: {l.ratio.toFixed(2)}
                </span>
              </div>
              <div className="flex gap-1 h-2">
                <div className="flex-1 rounded-full bg-[var(--bg-base)] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--accent-green)]"
                    style={{ width: `${(l.bidLiquidity / 250) * 100}%` }}
                  />
                </div>
                <div className="flex-1 rounded-full bg-[var(--bg-base)] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--accent-red)]"
                    style={{ width: `${(l.askLiquidity / 250) * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-between text-[8px] font-mono text-[var(--text-muted)] mt-0.5">
                <span>Bid ${l.bidLiquidity}M</span>
                <span>Ask ${l.askLiquidity}M</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-[var(--border-subtle)]">
          <div className="flex items-center justify-between text-[9px] font-mono text-[var(--text-muted)]">
            <span>Overall Liquidity Score</span>
            <span className="text-[var(--accent-blue)]">{overallScore}/100</span>
          </div>
          <Progress
            value={overallScore}
            indicatorClassName="h-full rounded-full bg-[var(--accent-blue)]"
            className="h-1.5 mt-1"
          />
        </div>
      </CardContent>
    </Card>
  );
}

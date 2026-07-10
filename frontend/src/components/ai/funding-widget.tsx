import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface FundingRate {
  symbol: string;
  rate: number;
  apr: number;
  timeToSettlement: string;
  sentiment: "bullish" | "bearish" | "neutral";
}

interface FundingWidgetProps {
  rates?: FundingRate[];
}

export function FundingWidget({ rates = [] }: FundingWidgetProps) {
  if (rates.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Funding Rates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No funding data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          Funding Rates
          <span className="text-[9px] font-mono text-[var(--text-muted)] ml-2">
            8h avg
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {rates.map((r) => (
            <div key={r.symbol}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                  {r.symbol}
                </span>
                <div className="flex items-center gap-1.5">
                  <span className={`text-[10px] font-mono tabular-nums ${r.rate >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                    {(r.rate * 100).toFixed(4)}%
                  </span>
                  <Badge variant={r.sentiment === "bullish" ? "success" : r.sentiment === "bearish" ? "danger" : "warning"}>
                    {r.sentiment}
                  </Badge>
                </div>
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono text-[var(--text-muted)]">
                <span>APR: {r.apr.toFixed(1)}%</span>
                <span>Settlement: {r.timeToSettlement}</span>
              </div>
              <Progress
                value={50 + r.rate * 1000}
                indicatorClassName={`h-full rounded-full ${r.rate >= 0 ? "bg-[var(--accent-green)]" : "bg-[var(--accent-red)]"}`}
                className="h-1 mt-1"
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";

interface TradeMetric {
  label: string;
  value: string;
  pct: number;
  positive: boolean;
}

interface PostTradeAnalysisProps {
  metrics?: TradeMetric[];
}

export function PostTradeAnalysis({
  metrics = [
    { label: "Win Rate", value: "68.5%", pct: 68.5, positive: true },
    { label: "Avg Win", value: "$245.30", pct: 72, positive: true },
    { label: "Avg Loss", value: "$112.40", pct: 28, positive: false },
    { label: "Profit Factor", value: "2.18", pct: 68, positive: true },
    { label: "Sharpe Ratio", value: "1.85", pct: 62, positive: true },
    { label: "Max Drawdown", value: "12.4%", pct: 12.4, positive: false },
    { label: "Avg Hold Time", value: "4h 23m", pct: 45, positive: false },
  ],
}: PostTradeAnalysisProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Post-Trade Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {metrics.map((m) => (
          <div key={m.label}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[12px] font-mono text-[var(--text-secondary)]">{m.label}</span>
              <span className={`text-[12px] font-mono tabular-nums ${m.positive ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                {m.value}
              </span>
            </div>
            <Progress
              value={m.pct}
              indicatorClassName={`h-full rounded-full ${m.positive ? "bg-[var(--accent-green)]" : "bg-[var(--accent-red)]"}`}
              className="h-1"
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

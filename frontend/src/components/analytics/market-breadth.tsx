import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface BreadthMetric {
  name: string;
  value: number;
  change: number;
  sentiment: "positive" | "negative" | "neutral";
}

interface MarketBreadthProps {
  metrics?: BreadthMetric[];
}

export function MarketBreadth({
  metrics = [
    { name: "Advancers", value: 65, change: 8, sentiment: "positive" },
    { name: "Decliners", value: 35, change: -8, sentiment: "negative" },
    { name: "Above 20MA", value: 58, change: 5, sentiment: "positive" },
    { name: "Above 50MA", value: 52, change: 3, sentiment: "positive" },
    { name: "New Highs", value: 22, change: 6, sentiment: "positive" },
    { name: "New Lows", value: 8, change: -4, sentiment: "positive" },
  ],
}: MarketBreadthProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Market Breadth</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {metrics.map((m) => (
          <div key={m.name}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[12px] font-mono text-[var(--text-secondary)]">{m.name}</span>
              <div className="flex items-center gap-1.5">
                <span className="text-[12px] font-mono tabular-nums text-[var(--text-primary)]">{m.value}%</span>
                <span className={`text-[12px] font-mono ${m.change >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {m.change >= 0 ? "+" : ""}{m.change}
                </span>
              </div>
            </div>
            <Progress
              value={m.value}
              indicatorClassName={`h-full rounded-full ${m.value >= 60 ? "bg-[var(--accent-green)]" : m.value >= 40 ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-red)]"}`}
              className="h-1"
            />
          </div>
        ))}
        <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[12px] font-mono">
          <span className="text-[var(--text-muted)]">Breadth Score</span>
          <Badge variant={metrics.filter((m) => m.sentiment === "positive").length > metrics.length / 2 ? "success" : "danger"}>
            {metrics.filter((m) => m.sentiment === "positive").length}/{metrics.length} positive
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

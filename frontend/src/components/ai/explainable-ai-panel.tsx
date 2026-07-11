import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface FactorContribution {
  factor: string;
  impact: number;
  direction: "positive" | "negative";
  description: string;
}

interface ExplainableAIPanelProps {
  symbol?: string;
  prediction?: string;
  confidence?: number;
  factors?: FactorContribution[];
}

export function ExplainableAIPanel({
  symbol = "BTC/USDT",
  prediction = "PENDING",
  confidence = 0,
  factors = [],
}: ExplainableAIPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Explainable AI</CardTitle>
          <Badge variant={prediction === "BULLISH" ? "success" : prediction === "BEARISH" ? "danger" : "default"}>
            {prediction} {confidence}%
          </Badge>
        </div>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {symbol}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          Factor Contributions
        </div>
        {factors.map((f) => (
          <div key={f.factor}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <span
                  className={`text-[9px] ${f.direction === "positive" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}
                >
                  {f.direction === "positive" ? "▲" : "▼"}
                </span>
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                  {f.factor}
                </span>
              </div>
              <span
                className={`text-[10px] font-mono tabular-nums ${
                  f.direction === "positive" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                }`}
              >
                {f.impact > 0 ? "+" : ""}{f.impact}%
              </span>
            </div>
            <Progress
              value={Math.abs(f.impact)}
              indicatorClassName={`h-full rounded-full transition-all ${
                f.direction === "positive" ? "bg-[var(--accent-green)]" : "bg-[var(--accent-red)]"
              }`}
              className="h-1.5"
            />
            <div className="text-[9px] text-[var(--text-muted)] mt-0.5">
              {f.description}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

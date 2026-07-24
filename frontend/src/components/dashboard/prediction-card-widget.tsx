import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface Prediction {
  symbol: string;
  direction: "UP" | "DOWN";
  confidence: number;
  timeframe: string;
  target: number;
  current: number;
}

interface PredictionCardWidgetProps {
  predictions?: Prediction[];
}

export function PredictionCardWidget({ predictions = [] }: PredictionCardWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Predictions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {predictions.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No predictions available
          </div>
        ) : (
          predictions.slice(0, 4).map((p) => (
            <div
              key={p.symbol}
              className="p-2 rounded-lg bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)]"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono font-medium text-[var(--text-primary)]">
                  {p.symbol}
                </span>
                <Badge variant={p.direction === "UP" ? "success" : "danger"}>
                  {p.direction}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-[12px] font-mono text-[var(--text-muted)]">
                <span>Target: ${p.target.toLocaleString()}</span>
                <span>Current: ${p.current.toLocaleString()}</span>
              </div>
              <div className="mt-1.5">
                <div className="flex justify-between text-[12px] font-mono text-[var(--text-muted)] mb-0.5">
                  <span>Confidence</span>
                  <span>{p.confidence.toFixed(0)}%</span>
                </div>
                <div className="h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-purple)]"
                    style={{ width: `${p.confidence}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { formatUSD } from "../../lib/utils";

interface StressScenario {
  name: string;
  impact: number;
  probability: "LOW" | "MEDIUM" | "HIGH";
}

interface StressTestWidgetProps {
  scenarios?: StressScenario[];
  worstCaseLoss?: number;
}

export function StressTestWidget({
  scenarios = [],
  worstCaseLoss = 0,
}: StressTestWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Stress Test</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {scenarios.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No stress test data
          </div>
        ) : (
          scenarios.slice(0, 4).map((s) => (
            <div key={s.name} className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                  {s.name}
                </span>
                <Badge
                  variant={
                    s.probability === "LOW"
                      ? "success"
                      : s.probability === "MEDIUM"
                        ? "warning"
                        : "danger"
                  }
                >
                  {s.probability}
                </Badge>
              </div>
              <span className="text-[10px] font-mono tabular-nums text-[var(--accent-red)]">
                {formatUSD(Math.abs(s.impact))}
              </span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface AnalysisItem {
  label: string;
  value: string;
  score: number;
  status: "bullish" | "bearish" | "neutral";
}

interface AnalysisDashboardProps {
  symbol?: string;
  items?: AnalysisItem[];
}

export function AnalysisDashboard({
  symbol = "BTC/USDT",
  items = [],
}: AnalysisDashboardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Analysis</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {symbol}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No analysis data
          </div>
        ) : (
          items.map((item) => (
            <div key={item.label}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-[var(--text-secondary)] uppercase tracking-wider">
                  {item.label}
                </span>
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-mono tabular-nums text-[var(--text-primary)]">
                    {item.value}
                  </span>
                  <Badge
                    variant={
                      item.status === "bullish"
                        ? "success"
                        : item.status === "bearish"
                          ? "danger"
                          : "warning"
                    }
                  >
                    {item.status}
                  </Badge>
                </div>
              </div>
              <Progress
                value={item.score}
                indicatorClassName="h-full rounded-full transition-all"
                className="h-1"
              />
            </div>
          ))
        )}

        <div className="pt-2 border-t border-[var(--border-subtle)]">
          <div className="text-[10px] font-mono text-[var(--text-muted)] mb-2">
            Sentiment Breakdown
          </div>
          <div className="flex h-2 rounded-full overflow-hidden">
            <div
              className="bg-[var(--accent-green)] transition-all"
              style={{ width: "58%" }}
            />
            <div
              className="bg-[var(--accent-yellow)] transition-all"
              style={{ width: "22%" }}
            />
            <div
              className="bg-[var(--accent-red)] transition-all"
              style={{ width: "20%" }}
            />
          </div>
          <div className="flex justify-between text-[9px] font-mono text-[var(--text-muted)] mt-1">
            <span>Bullish 58%</span>
            <span>Neutral 22%</span>
            <span>Bearish 20%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

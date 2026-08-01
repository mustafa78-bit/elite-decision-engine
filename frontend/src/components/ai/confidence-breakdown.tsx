import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";

interface ConfidenceMetric {
  label: string;
  value: number;
  weight: number;
}

interface ConfidenceBreakdownProps {
  overall?: number;
  metrics?: ConfidenceMetric[];
}

export function ConfidenceBreakdown({
  overall = 78,
  metrics = [
    { label: "Technical Analysis", value: 85, weight: 0.35 },
    { label: "Market Regime", value: 72, weight: 0.20 },
    { label: "Volume Profile", value: 80, weight: 0.15 },
    { label: "Sentiment Analysis", value: 65, weight: 0.15 },
    { label: "On-Chain Data", value: 70, weight: 0.15 },
  ],
}: ConfidenceBreakdownProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Confidence Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
          <div className="relative w-14 h-14">
            <svg className="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--border-subtle)" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15.5" fill="none"
                stroke="var(--accent-blue)" strokeWidth="3"
                strokeDasharray={`${overall * 0.97} ${100 - overall * 0.97}`}
                strokeLinecap="round"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-xs font-mono font-bold text-[var(--text-primary)]">
              {overall}%
            </span>
          </div>
          <div>
            <div className="text-xs font-medium text-[var(--text-primary)]">
              Overall Confidence
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">
              Weighted across {metrics.length} factors
            </div>
          </div>
        </div>

        {metrics.map((m) => (
          <div key={m.label}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                {m.label}
              </span>
              <span className="text-[10px] font-mono tabular-nums text-[var(--text-muted)]">
                {m.value}%
                <span className="text-[8px] ml-1">
                  ({(m.weight * 100).toFixed(0)}%)
                </span>
              </span>
            </div>
            <Progress
              value={m.value}
              indicatorClassName="h-full rounded-full bg-[var(--accent-blue)]"
              className="h-1"
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

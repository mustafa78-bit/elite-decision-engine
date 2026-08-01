import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface RiskMetric {
  label: string;
  value: string;
  status: "good" | "warning" | "danger";
}

interface RiskWidgetProps {
  riskMetrics?: RiskMetric[];
  overallRisk?: string;
}

const statusColor: Record<string, string> = {
  good: "var(--accent-green)",
  warning: "var(--accent-yellow)",
  danger: "var(--accent-red)",
};

export function RiskWidget({
  riskMetrics = [],
  overallRisk,
}: RiskWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Risk</CardTitle>
        {overallRisk != null ? (
          <Badge
            variant={
              overallRisk === "LOW"
                ? "success"
                : overallRisk === "MEDIUM"
                  ? "warning"
                  : "danger"
            }
          >
            {overallRisk}
          </Badge>
        ) : (
          <span className="text-[10px] font-mono text-[var(--text-muted)]">--</span>
        )}
      </CardHeader>
      <CardContent>
        {riskMetrics.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No risk data
          </div>
        ) : (
          <div className="space-y-2">
            {riskMetrics.map((m) => (
              <div key={m.label}>
                <div className="flex justify-between text-[11px] mb-0.5">
                  <span className="text-[var(--text-secondary)]">
                    {m.label}
                  </span>
                  <span className="font-mono text-[var(--text-primary)]">
                    {m.value}
                  </span>
                </div>
                <div className="h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: "60%",
                      background: statusColor[m.status] || "var(--accent-yellow)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface HealthMetric {
  label: string;
  value: number;
  status: "good" | "warning" | "danger";
}

interface HealthWidgetProps {
  metrics?: HealthMetric[];
  overallScore?: number;
}

export function HealthWidget({
  metrics = [],
  overallScore,
}: HealthWidgetProps) {
  const scoreColor = overallScore != null
    ? overallScore >= 80
      ? "var(--accent-green)"
      : overallScore >= 50
        ? "var(--accent-yellow)"
        : "var(--accent-red)"
    : "var(--text-muted)";

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Health</CardTitle>
        <span
          className="text-lg font-mono font-bold tabular-nums"
          style={{ color: scoreColor }}
        >
          {overallScore != null ? overallScore.toFixed(0) : "--"}
        </span>
      </CardHeader>
      <CardContent>
        {metrics.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No health data
          </div>
        ) : (
          <div className="space-y-2">
            {metrics.map((m) => (
              <div key={m.label}>
                <div className="flex justify-between text-[11px] mb-0.5">
                  <span className="text-[var(--text-secondary)]">
                    {m.label}
                  </span>
                  <span
                    className="font-mono"
                    style={{
                      color:
                        m.status === "good"
                          ? "var(--accent-green)"
                          : m.status === "warning"
                            ? "var(--accent-yellow)"
                            : "var(--accent-red)",
                    }}
                  >
                    {m.value.toFixed(0)}%
                  </span>
                </div>
                <div className="h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${m.value}%`,
                      backgroundColor:
                        m.status === "good"
                          ? "var(--accent-green)"
                          : m.status === "warning"
                            ? "var(--accent-yellow)"
                            : "var(--accent-red)",
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

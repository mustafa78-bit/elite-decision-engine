import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface ExecMetric {
  label: string;
  value: string;
  trend: "up" | "down" | "stable";
  status: "good" | "warning" | "bad";
}

interface ExecutionAnalyticsProps {
  metrics?: ExecMetric[];
}

export function ExecutionAnalytics({
  metrics = [
    { label: "Fill Rate", value: "97.2%", trend: "up", status: "good" },
    { label: "Avg Slippage", value: "0.03%", trend: "down", status: "good" },
    { label: "Orders/Min", value: "2.4", trend: "stable", status: "good" },
    { label: "Cancel Rate", value: "8.1%", trend: "down", status: "good" },
    { label: "Latency (ms)", value: "12", trend: "up", status: "warning" },
    { label: "Rejection Rate", value: "0.5%", trend: "stable", status: "good" },
  ],
}: ExecutionAnalyticsProps) {
  const trendIcon = { up: "▲", down: "▼", stable: "◆" };
  const statusColor = { good: "success" as const, warning: "warning" as const, bad: "danger" as const };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Execution Analytics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {metrics.map((m) => (
          <div key={m.label} className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <span className="text-[10px] font-mono text-[var(--text-secondary)]">{m.label}</span>
            <div className="flex items-center gap-2">
              <span className={`text-[9px] ${m.trend === "up" ? "text-[var(--accent-green)]" : m.trend === "down" ? "text-[var(--accent-red)]" : "text-[var(--text-muted)]"}`}>
                {trendIcon[m.trend]}
              </span>
              <span className="text-[10px] font-mono tabular-nums text-[var(--text-primary)]">{m.value}</span>
              <Badge variant={statusColor[m.status]} className="text-[8px]">{m.status}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

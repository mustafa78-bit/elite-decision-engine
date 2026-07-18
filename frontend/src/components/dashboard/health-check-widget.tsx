import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface CheckItem {
  name: string;
  status: "PASS" | "FAIL" | "WARN";
  detail?: string;
}

interface HealthCheckWidgetProps {
  checks?: CheckItem[];
  overallStatus?: "HEALTHY" | "DEGRADED" | "DOWN";
}

const statusBadge: Record<string, "success" | "danger" | "warning"> = {
  PASS: "success",
  FAIL: "danger",
  WARN: "warning",
};

export function HealthCheckWidget({
  checks = [],
  overallStatus,
}: HealthCheckWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Health Checks</CardTitle>
        {overallStatus != null ? (
          <Badge
            variant={
              overallStatus === "HEALTHY"
                ? "success"
                : overallStatus === "DEGRADED"
                  ? "warning"
                  : "danger"
            }
          >
            {overallStatus}
          </Badge>
        ) : (
          <span className="text-[10px] font-mono text-[var(--text-muted)]">--</span>
        )}
      </CardHeader>
      <CardContent>
        {checks.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No health check data
          </div>
        ) : (
          <div className="space-y-1">
            {checks.map((c) => (
              <div
                key={c.name}
                className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0"
              >
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{
                      backgroundColor:
                        c.status === "PASS"
                          ? "var(--accent-green)"
                          : c.status === "FAIL"
                            ? "var(--accent-red)"
                            : "var(--accent-yellow)",
                    }}
                  />
                  <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                    {c.name}
                  </span>
                </div>
                <Badge variant={statusBadge[c.status]}>{c.status}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

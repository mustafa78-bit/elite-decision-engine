import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface ErrorRateWidgetProps {
  errorRate?: number;
  totalErrors?: number;
  totalRequests?: number;
  lastError?: string;
  lastErrorTime?: string;
}

export function ErrorRateWidget({
  errorRate = 0,
  totalErrors = 0,
  totalRequests = 0,
  lastError = "",
  lastErrorTime = "",
}: ErrorRateWidgetProps) {
  const status =
    errorRate < 0.01
      ? "good"
      : errorRate < 0.05
        ? "warning"
        : "danger";

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Error Rate</CardTitle>
        <Badge variant={status === "good" ? "success" : status === "warning" ? "warning" : "danger"}>
          {(errorRate * 100).toFixed(2)}%
        </Badge>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-[12px] text-[var(--text-muted)]">Total Errors</div>
            <div className="text-sm font-mono tabular-nums text-[var(--accent-red)]">
              {totalErrors}
            </div>
          </div>
          <div>
            <div className="text-[12px] text-[var(--text-muted)]">Total Requests</div>
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {totalRequests}
            </div>
          </div>
        </div>
        {lastError && (
          <div className="p-2 rounded-lg bg-[var(--accent-red)]/5 border border-[var(--accent-red)]/10">
            <div className="text-[12px] text-[var(--text-muted)]">Last Error</div>
            <div className="text-[12px] font-mono text-[var(--accent-red)] truncate">
              {lastError}
            </div>
            {lastErrorTime && (
              <div className="text-[12px] font-mono text-[var(--text-muted)] mt-0.5">
                {lastErrorTime}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

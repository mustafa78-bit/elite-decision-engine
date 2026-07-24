import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface EndpointLimit {
  endpoint: string;
  limit: number;
  used: number;
  remaining: number;
  resetIn: string;
  status: "ok" | "warn" | "critical";
}

export function RateLimitMonitor() {
  const endpoints: EndpointLimit[] = [
    { endpoint: "GET /api/v1/orders", limit: 1200, used: 342, remaining: 858, resetIn: "58s", status: "ok" },
    { endpoint: "POST /api/v1/orders", limit: 300, used: 245, remaining: 55, resetIn: "42s", status: "warn" },
    { endpoint: "GET /api/v1/positions", limit: 1800, used: 421, remaining: 1379, resetIn: "1m 12s", status: "ok" },
    { endpoint: "GET /api/v1/ticker", limit: 600, used: 589, remaining: 11, resetIn: "23s", status: "critical" },
    { endpoint: "WEBSOCKET", limit: 100, used: 48, remaining: 52, resetIn: "N/A", status: "ok" },
  ];

  return (
    <Card className="h-full">
      <CardHeader><CardTitle>Rate Limit Monitor</CardTitle></CardHeader>
      <CardContent className="space-y-1.5">
        {endpoints.map((ep, i) => {
          const usage = (ep.used / ep.limit) * 100;
          return (
            <div key={i} className="p-1.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[12px] font-mono text-[var(--text-secondary)]">{ep.endpoint}</span>
                <Badge variant={ep.status === "critical" ? "danger" : ep.status === "warn" ? "warning" : "success"} className="text-[11px]">{ep.remaining} left</Badge>
              </div>
              <Progress
                value={usage}
                indicatorClassName={`h-full rounded-full ${usage > 90 ? "bg-[var(--accent-red)]" : usage > 70 ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-blue)]"}`}
                className="h-1"
              />
              <div className="flex justify-between text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                <span>{ep.used}/{ep.limit}</span>
                <span>Reset: {ep.resetIn}</span>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface ErrorItem {
  id: string;
  type: string;
  message: string;
  source: string;
  count: number;
  firstSeen: string;
  lastSeen: string;
  severity: "critical" | "error" | "warning";
  resolved: boolean;
}

interface ErrorDashboardProps {
  errors?: ErrorItem[];
}

export function ErrorDashboard({
  errors = [
    { id: "1", type: "API_TIMEOUT", message: "GET /api/v1/orders timed out", source: "Binance", count: 24, firstSeen: "2026-07-08", lastSeen: "5m ago", severity: "error", resolved: false },
    { id: "2", type: "WEBSOCKET_DISCONNECT", message: "WebSocket disconnected unexpectedly", source: "Bybit", count: 8, firstSeen: "2026-07-09", lastSeen: "1h ago", severity: "warning", resolved: false },
    { id: "3", type: "ORDER_REJECTED", message: "Insufficient margin for order", source: "System", count: 3, firstSeen: "2026-07-09", lastSeen: "3h ago", severity: "error", resolved: true },
    { id: "4", type: "RATE_LIMIT", message: "Rate limit exceeded on ticker endpoint", source: "OKX", count: 15, firstSeen: "2026-07-07", lastSeen: "1d ago", severity: "warning", resolved: true },
  ],
}: ErrorDashboardProps) {
  const activeCount = errors.filter((e) => !e.resolved).length;
  const criticalCount = errors.filter((e) => !e.resolved && e.severity === "critical").length;

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Error Dashboard</CardTitle>
          <div className="flex items-center gap-1.5">
            {criticalCount > 0 && <Badge variant="danger">{criticalCount} critical</Badge>}
            <Badge variant={activeCount > 0 ? "warning" : "success"}>{activeCount} active</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-1.5 max-h-64 overflow-y-auto">
        {errors.map((e) => (
          <div key={e.id} className={`p-2 rounded-lg border text-[9px] font-mono ${e.resolved ? "bg-[var(--bg-base)]/50 border-[var(--border-subtle)] opacity-50" : "bg-[var(--bg-base)] border-[var(--border-subtle)]"}`}>
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1">
                <span className={`w-1.5 h-1.5 rounded-full ${e.severity === "critical" ? "bg-[var(--accent-red)]" : e.severity === "error" ? "bg-red-400" : "bg-[var(--accent-yellow)]"}`} />
                <span className="text-[var(--text-secondary)]">{e.type}</span>
                <Badge variant={e.severity === "critical" ? "danger" : e.severity === "error" ? "danger" : "warning"} className="text-[7px]">{e.severity}</Badge>
                {e.resolved && <span className="text-[var(--accent-green)] text-[8px]">resolved</span>}
              </div>
              <span className="text-[var(--text-muted)]">x{e.count}</span>
            </div>
            <div className="text-[var(--text-muted)] mb-0.5">{e.message}</div>
            <div className="text-[var(--text-muted)]/60">{e.source} · Last: {e.lastSeen}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

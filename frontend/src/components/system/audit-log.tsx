import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface LogEntry {
  id: string;
  action: string;
  user: string;
  resource: string;
  details: string;
  ip: string;
  timestamp: string;
  severity: "info" | "warning" | "error";
}

interface AuditLogProps {
  logs?: LogEntry[];
}

export function AuditLog({
  logs = [
    { id: "1", action: "ORDER_CREATED", user: "alice@e.com", resource: "order:12345", details: "Buy 0.5 BTC @ $42,890", ip: "192.168.1.100", timestamp: "2m ago", severity: "info" },
    { id: "2", action: "API_KEY_CREATED", user: "bob@e.com", resource: "apikey:678", details: "Binance main key added", ip: "10.0.0.50", timestamp: "15m ago", severity: "info" },
    { id: "3", action: "POSITION_CLOSED", user: "system", resource: "position:456", details: "SL triggered - BTC long closed", ip: "internal", timestamp: "1h ago", severity: "warning" },
    { id: "4", action: "LOGIN_FAILED", user: "unknown", resource: "session", details: "Invalid password x3", ip: "45.33.32.156", timestamp: "3h ago", severity: "error" },
  ],
}: AuditLogProps) {
  return (
    <Card className="h-full">
      <CardHeader><CardTitle>Audit Log</CardTitle></CardHeader>
      <CardContent className="max-h-64 overflow-y-auto space-y-1">
        {logs.map((l) => (
          <div key={l.id} className="p-1.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[12px] font-mono">
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1">
                <span className={`w-1 h-1 rounded-full ${l.severity === "error" ? "bg-[var(--accent-red)]" : l.severity === "warning" ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-blue)]"}`} />
                <span className="text-[var(--text-secondary)]">{l.action}</span>
                <Badge variant={l.severity === "error" ? "danger" : l.severity === "warning" ? "warning" : "info"} className="text-[11px]">{l.severity}</Badge>
              </div>
              <span className="text-[var(--text-muted)]">{l.timestamp}</span>
            </div>
            <div className="text-[var(--text-muted)] mb-0.5">{l.details}</div>
            <div className="text-[var(--text-muted)]/60">{l.user} · {l.ip}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

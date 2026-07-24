import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface UserSession {
  user: string;
  role: string;
  status: "active" | "idle" | "away";
  currentPage: string;
  ip: string;
  loginTime: string;
  activity: number;
}

interface UserActivityProps {
  sessions?: UserSession[];
}

export function UserActivity({
  sessions = [
    { user: "alice@e.com", role: "Trader", status: "active", currentPage: "/trading/BTCUSDT", ip: "192.168.1.100", loginTime: "2h ago", activity: 95 },
    { user: "bob@e.com", role: "Admin", status: "idle", currentPage: "/admin/settings", ip: "10.0.0.50", loginTime: "4h ago", activity: 30 },
    { user: "carol@e.com", role: "Viewer", status: "away", currentPage: "/analytics", ip: "203.0.113.42", loginTime: "1d ago", activity: 5 },
  ],
}: UserActivityProps) {
  return (
    <Card className="h-full">
      <CardHeader><CardTitle>User Activity</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {sessions.map((s, i) => (
          <div key={i} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${s.status === "active" ? "bg-[var(--accent-green)]" : s.status === "idle" ? "bg-[var(--accent-yellow)]" : "bg-[var(--text-muted)]"}`} />
                <span className="text-[12px] font-mono text-[var(--text-secondary)]">{s.user}</span>
                <Badge variant="default" className="text-[11px]">{s.role}</Badge>
              </div>
              <span className="text-[11px] text-[var(--text-muted)]">{s.loginTime}</span>
            </div>
            <div className="text-[12px] font-mono text-[var(--text-muted)] mb-1">{s.currentPage}</div>
            <div className="flex items-center gap-2">
              <Progress value={s.activity} indicatorClassName="h-full rounded-full bg-[var(--accent-blue)]" className="flex-1 h-1" />
              <span className="text-[11px] font-mono text-[var(--text-muted)]">{s.activity}%</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

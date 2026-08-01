import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface NotificationStatsWidgetProps {
  total?: number;
  unread?: number;
  today?: number;
  byType?: Record<string, number>;
}

export function NotificationStatsWidget({
  total = 0,
  unread = 0,
  today = 0,
  byType = {},
}: NotificationStatsWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Notification Stats</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="text-center p-2 rounded-lg bg-[var(--bg-elevated)]/50">
            <div className="text-lg font-mono font-bold tabular-nums text-[var(--text-primary)]">
              {total}
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">Total</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[var(--bg-elevated)]/50">
            <div className="text-lg font-mono font-bold tabular-nums text-[var(--accent-blue)]">
              {unread}
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">Unread</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[var(--bg-elevated)]/50">
            <div className="text-lg font-mono font-bold tabular-nums text-[var(--accent-green)]">
              {today}
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">Today</div>
          </div>
        </div>
        {Object.keys(byType).length > 0 && (
          <div className="space-y-1">
            {Object.entries(byType).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-[var(--text-secondary)] uppercase">
                  {type}
                </span>
                <span className="text-[10px] font-mono tabular-nums text-[var(--text-primary)]">
                  {count}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

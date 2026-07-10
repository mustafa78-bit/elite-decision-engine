import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { formatTime } from "../../lib/utils";

interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  status?: string;
}

interface RecentActivityWidgetProps {
  activities?: Activity[];
}

const activityBadge: Record<string, "success" | "danger" | "warning" | "info"> = {
  trade: "success",
  signal: "info",
  risk: "warning",
  error: "danger",
  order: "purple",
};

export function RecentActivityWidget({
  activities = [],
}: RecentActivityWidgetProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="max-h-64 overflow-y-auto">
        {activities.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No recent activity
          </div>
        ) : (
          <div className="space-y-1">
            {activities.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0"
              >
                <div className="flex items-center gap-2">
                  <Badge
                    variant={activityBadge[a.type] || "default"}
                  >
                    {a.type}
                  </Badge>
                  <span className="text-xs text-[var(--text-secondary)]">
                    {a.description}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[var(--text-muted)]">
                  {formatTime(a.timestamp)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

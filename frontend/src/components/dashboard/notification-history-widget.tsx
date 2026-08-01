import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { formatTime } from "../../lib/utils";

interface HistoryItem {
  id: string;
  event: string;
  type: string;
  timestamp: string;
  read: boolean;
}

interface NotificationHistoryWidgetProps {
  items?: HistoryItem[];
}

const typeBadge: Record<string, "success" | "danger" | "warning" | "info"> = {
  trade: "success",
  risk: "warning",
  error: "danger",
  signal: "info",
  system: "info",
};

export function NotificationHistoryWidget({ items = [] }: NotificationHistoryWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Notification History</CardTitle>
      </CardHeader>
      <CardContent className="max-h-64 overflow-y-auto">
        {items.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No notification history
          </div>
        ) : (
          <div className="space-y-0.5">
            {items.slice(0, 15).map((item) => (
              <div
                key={item.id}
                className={`flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0 ${
                  item.read ? "opacity-50" : ""
                }`}
              >
                <div className="flex items-center gap-2">
                  {!item.read && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] shrink-0" />
                  )}
                  <Badge variant={typeBadge[item.type] || "info"}>
                    {item.type}
                  </Badge>
                  <span className="text-[10px] text-[var(--text-secondary)]">
                    {item.event}
                  </span>
                </div>
                <span className="text-[9px] font-mono text-[var(--text-muted)]">
                  {formatTime(item.timestamp)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

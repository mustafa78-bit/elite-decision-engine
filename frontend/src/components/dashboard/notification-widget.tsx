import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchNotificationsWidget } from "../../api/widgets";
import { formatTime } from "../../lib/utils";

export function NotificationWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["notifications-widget"],
    queryFn: () => fetchNotificationsWidget(8),
    refetchInterval: 15_000,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        {data && data.unread > 0 && (
          <Badge variant="warning">{data.unread} new</Badge>
        )}
      </CardHeader>
      <CardContent className="max-h-64 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : !data || data.notifications.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No notifications
          </div>
        ) : (
          <div className="space-y-1">
            {data.notifications.map((n) => (
              <div
                key={n.id}
                className={`flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0 ${
                  n.read ? "opacity-50" : ""
                }`}
              >
                <div className="flex items-center gap-2">
                  {!n.read && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] shrink-0" />
                  )}
                  <span className="text-xs font-mono text-[var(--text-secondary)]">
                    {n.event_type}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[var(--text-muted)]">
                  {formatTime(n.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

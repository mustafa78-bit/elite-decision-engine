import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchNotificationsWidget } from "../../api/widgets";
import type { NotificationItemDTO } from "../../types/api/widget";

export function NotificationPanel() {
  const [items, setItems] = useState<NotificationItemDTO[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await fetchNotificationsWidget(5);
      setItems(res.notifications);
      setUnread(res.unread);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Notifications</CardTitle>
          {unread > 0 && (
            <Badge variant="warning">{unread} unread</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : items.length === 0 ? (
          <p className="text-[10px] text-gray-600 font-mono">No notifications</p>
        ) : (
          <div className="space-y-1">
            {items.map((n) => (
              <div
                key={n.id}
                className={`flex items-center justify-between py-1 border-b border-gray-800 last:border-0 ${n.read ? "opacity-50" : ""}`}
              >
                <div className="flex items-center gap-2">
                  {!n.read && <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />}
                  <span className="text-[10px] font-mono text-gray-300">
                    {n.event_type}
                  </span>
                </div>
                <span className="text-[9px] text-gray-600 font-mono">
                  {n.created_at ? new Date(n.created_at).toLocaleTimeString() : ""}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

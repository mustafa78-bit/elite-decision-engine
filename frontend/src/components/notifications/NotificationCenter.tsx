import { useCallback, useEffect, useState } from "react";

import type { NotificationRow } from "../../api/notifications";
import { fetchNotifications, markNotificationRead } from "../../api/notifications";
import NotificationItem from "./NotificationItem";

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState<NotificationRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchNotifications();
      setNotifications(data);
    } catch {
      setError("Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleMarkRead = useCallback(async (id: number) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
      );
    } catch {
      // ignore
    }
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading notifications...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
        {error}
        <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">
          Retry
        </button>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        No notifications yet
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500">
          {unreadCount > 0 ? `${unreadCount} unread` : "All read"}
        </span>
      </div>
      <div className="border border-gray-800 rounded divide-y divide-gray-800">
        {notifications.map((n) => (
          <NotificationItem key={n.id} notification={n} onMarkRead={handleMarkRead} />
        ))}
      </div>
    </div>
  );
}

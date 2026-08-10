import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchNotifications, markNotificationRead } from "../../api/notifications";
import type { NotificationDetailDTO } from "../../types/api/notifications";
import NotificationItem from "./NotificationItem";

export default function NotificationCenter() {
  const { t } = useTranslation("notifications");
  const [notifications, setNotifications] = useState<NotificationDetailDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchNotifications();
      setNotifications(data.notifications);
    } catch {
      setError(t("center.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [t]);

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
        {t("center.loading")}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/30 bg-[var(--accent-red)]/10 rounded">
        {error}
        <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">
          {t("center.retry")}
        </button>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        {t("center.empty")}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500">
          {unreadCount > 0 ? t("center.unreadCount", { count: unreadCount }) : t("center.allRead")}
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

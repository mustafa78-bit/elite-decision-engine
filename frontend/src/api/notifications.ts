import { apiFetch } from "./client";

export interface NotificationRow {
  id: number;
  event_type: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string | null;
}

export function fetchNotifications(limit = 50): Promise<NotificationRow[]> {
  return apiFetch<NotificationRow[]>(`/notifications?limit=${limit}`);
}

export function markNotificationRead(id: number): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/notifications/${id}/read`, {
    method: "PUT",
  });
}

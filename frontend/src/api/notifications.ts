import { apiFetch } from "./client";
import type { NotificationDetailDTO, NotificationStatsDTO } from "../types/api/notifications";

export interface NotificationRow {
  id: number;
  event_type: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string | null;
}

export function fetchNotifications(limit = 50, offset = 0): Promise<{ notifications: NotificationDetailDTO[]; total: number; offset: number; limit: number }> {
  return apiFetch(`/notifications?limit=${limit}&offset=${offset}`);
}

export function fetchNotification(id: number): Promise<NotificationDetailDTO> {
  return apiFetch(`/notifications/${id}`);
}

export function fetchNotificationStats(): Promise<NotificationStatsDTO> {
  return apiFetch("/notifications/stats");
}

export function markNotificationRead(id: number): Promise<{ success: boolean }> {
  return apiFetch(`/notifications/${id}/read`, { method: "PUT" });
}

export function markAllNotificationsRead(): Promise<{ success: boolean }> {
  return apiFetch("/notifications/read-all", { method: "PUT" });
}

export function deleteNotification(id: number): Promise<{ success: boolean }> {
  return apiFetch(`/notifications/${id}`, { method: "DELETE" });
}

export function deleteAllReadNotifications(): Promise<{ success: boolean }> {
  return apiFetch("/notifications/read-all", { method: "DELETE" });
}

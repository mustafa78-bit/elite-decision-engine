export interface NotificationDetailDTO {
  id: number;
  user_id: number | null;
  event_type: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string | null;
}

export interface NotificationStatsDTO {
  total: number;
  unread: number;
  by_type: Record<string, number>;
}

export interface BulkNotificationActionDTO {
  ids?: number[];
  action: string;
}

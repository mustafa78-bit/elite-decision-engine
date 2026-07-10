export interface WidgetDTO {
  id: string;
  type: string;
  title: string;
  data: Record<string, unknown>;
}

export interface KPIDTO {
  name: string;
  value: number;
  previous_value?: number;
  change_pct?: number;
  unit: string;
  trend: string;
  status: string;
}

export interface PortfolioSummaryDTO {
  total_pnl: number;
  open_pnl: number;
  total_trades: number;
  open_trades: number;
  win_rate: number;
  avg_pnl: number;
  profit_factor: number;
}

export interface MonitoringStatusDTO {
  status: string;
  services: Record<string, string>;
}

export interface NotificationWidgetDTO {
  notifications: NotificationItemDTO[];
  total: number;
  unread: number;
}

export interface NotificationItemDTO {
  id: number;
  event_type: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string | null;
}

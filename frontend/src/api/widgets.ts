import { apiFetch } from "./client";
import type { WidgetDTO, KPIDTO, PortfolioSummaryDTO, MonitoringStatusDTO, NotificationItemDTO } from "../types/api/widget";

export function fetchWidgets(): Promise<{ widgets: WidgetDTO[] }> {
  return apiFetch("/widgets");
}

export function fetchWidget(id: string): Promise<{ widget: WidgetDTO }> {
  return apiFetch(`/widgets/${id}`);
}

export function fetchKpiWidget(): Promise<{ widget: WidgetDTO; kpis: KPIDTO[] }> {
  return apiFetch("/widgets/kpi");
}

export function fetchKpiDetail(): Promise<{ kpis: KPIDTO[] }> {
  return apiFetch("/widgets/kpi/detail");
}

export function fetchPortfolioSummary(): Promise<{ widget: WidgetDTO; portfolio: PortfolioSummaryDTO }> {
  return apiFetch("/widgets/portfolio");
}

export function fetchPortfolioWidgetSummary(): Promise<{ widget: WidgetDTO; portfolio: PortfolioSummaryDTO }> {
  return apiFetch("/widgets/portfolio/summary");
}

export function fetchMonitoringStatus(): Promise<{ widget: WidgetDTO; monitoring: MonitoringStatusDTO }> {
  return apiFetch("/widgets/monitoring");
}

export function fetchMonitoringWidgetStatus(): Promise<{ widget: WidgetDTO; monitoring: MonitoringStatusDTO }> {
  return apiFetch("/widgets/monitoring/status");
}

export function fetchNotificationsWidget(limit = 10): Promise<{ widget: WidgetDTO; notifications: NotificationItemDTO[]; total: number; unread: number }> {
  return apiFetch(`/widgets/notifications?limit=${limit}`);
}

export function fetchNotificationsWidgetRecent(limit = 10): Promise<{ widget: WidgetDTO; notifications: NotificationItemDTO[]; total: number; unread: number }> {
  return apiFetch(`/widgets/notifications/recent?limit=${limit}`);
}

import { apiFetch } from "./client";
import type { WidgetDTO, KPIDTO, PortfolioSummaryDTO, MonitoringStatusDTO, NotificationWidgetDTO, HeroBannerDTO } from "../types/api/widget";

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

// These 4 endpoints all return the flat DTO directly (services/widget_service.py's
// _portfolio_widget()/_monitoring_widget() -- no {widget, portfolio/monitoring}
// wrapper exists on any of them, regardless of route). Both /widgets/portfolio and
// /widgets/portfolio/summary (same for monitoring) hit the identical handler.
export function fetchPortfolioSummary(): Promise<PortfolioSummaryDTO> {
  return apiFetch("/widgets/portfolio");
}

export function fetchPortfolioWidgetSummary(): Promise<PortfolioSummaryDTO> {
  return apiFetch("/widgets/portfolio/summary");
}

export function fetchMonitoringStatus(): Promise<MonitoringStatusDTO> {
  return apiFetch("/widgets/monitoring");
}

export function fetchMonitoringWidgetStatus(): Promise<MonitoringStatusDTO> {
  return apiFetch("/widgets/monitoring/status");
}

export function fetchNotificationsWidget(limit = 10): Promise<NotificationWidgetDTO> {
  return apiFetch(`/widgets/notifications?limit=${limit}`);
}

export function fetchNotificationsWidgetRecent(limit = 10): Promise<NotificationWidgetDTO> {
  return apiFetch(`/widgets/notifications/recent?limit=${limit}`);
}

export function fetchHeroBanner(): Promise<HeroBannerDTO> {
  return apiFetch("/dashboard/hero");
}

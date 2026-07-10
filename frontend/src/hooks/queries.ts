import { useQuery } from "@tanstack/react-query";
import { fetchKpiDetail, fetchPortfolioWidgetSummary, fetchMonitoringWidgetStatus, fetchNotificationsWidget } from "../api/widgets";
import { fetchRegime } from "../api/regime";
import { fetchWatchlists } from "../api/watchlists";
import { fetchSignals } from "../api/signals";
import { fetchPortfolio } from "../api/portfolio";

export function useKpis() {
  return useQuery({
    queryKey: ["kpi-detail"],
    queryFn: fetchKpiDetail,
    refetchInterval: 10_000,
  });
}

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ["portfolio-summary"],
    queryFn: fetchPortfolioWidgetSummary,
    refetchInterval: 10_000,
  });
}

export function useRegime() {
  return useQuery({
    queryKey: ["regime"],
    queryFn: fetchRegime,
    refetchInterval: 30_000,
  });
}

export function useMonitoring() {
  return useQuery({
    queryKey: ["monitoring"],
    queryFn: fetchMonitoringWidgetStatus,
    refetchInterval: 15_000,
  });
}

export function useNotifications(limit = 10) {
  return useQuery({
    queryKey: ["notifications-widget", limit],
    queryFn: () => fetchNotificationsWidget(limit),
    refetchInterval: 15_000,
  });
}

export function useWatchlists() {
  return useQuery({
    queryKey: ["watchlists"],
    queryFn: fetchWatchlists,
    refetchInterval: 30_000,
  });
}

export function useSignals() {
  return useQuery({
    queryKey: ["signals"],
    queryFn: () => fetchSignals(),
    refetchInterval: 20_000,
  });
}

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: fetchPortfolio,
    refetchInterval: 10_000,
  });
}

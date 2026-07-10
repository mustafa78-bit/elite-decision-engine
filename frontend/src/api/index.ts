export { apiFetch, ApiError, BASE_URL } from "./client";
export type { KPIDTO, WidgetDTO, PortfolioSummaryDTO, MonitoringStatusDTO, NotificationItemDTO } from "../types/api/widget";
export type { PortfolioFullDTO, PortfolioDistributionDTO, PortfolioPerformanceDTO, PortfolioRiskDTO } from "../types/api/portfolio";
export type { UserPreferencesDTO, ThemeConfigDTO, LayoutConfigDTO } from "../types/api/preferences";
export type { WatchlistDTO, WatchlistCreateDTO, WatchlistUpdateDTO } from "../types/api/watchlist";
export type { TimelineResponseDTO, TimelineEventDTO } from "../types/api/timeline";
export type { NotificationDetailDTO, NotificationStatsDTO } from "../types/api/notifications";
export {
  fetchKpiDetail, fetchPortfolioWidgetSummary, fetchMonitoringWidgetStatus, fetchNotificationsWidget, fetchNotificationsWidgetRecent,
} from "./widgets";
export {
  fetchPortfolioSummary, fetchPortfolioDistribution, fetchPortfolioPerformance, fetchPortfolioRisk, fetchPortfolioFull,
} from "./portfolio_detail";
export {
  fetchPreferences, updatePreferences, updateTheme, updateLayout, fetchThemeConfig, fetchDefaultPreferences,
} from "./preferences";
export {
  fetchWatchlists, fetchWatchlist, createWatchlist, updateWatchlist, deleteWatchlist, addWatchlistSymbol, removeWatchlistSymbol,
} from "./watchlists";
export {
  fetchSignalTimeline, fetchTradeTimeline, fetchGlobalTimeline,
} from "./timeline";
export {
  markNotificationRead, markAllNotificationsRead, deleteNotification, deleteAllReadNotifications, fetchNotifications, fetchNotificationStats,
} from "./notifications_detail";

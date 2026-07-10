import { useCallback } from "react";

interface WidgetDefinition {
  id: string;
  name: string;
  description: string;
  category: "kpi" | "portfolio" | "risk" | "monitoring" | "ai" | "notification" | "chart" | "market";
  defaultWidth: 1 | 2 | 3 | 4;
  defaultHeight: 1 | 2;
  component: string;
}

const widgetCatalog: WidgetDefinition[] = [
  { id: "kpi", name: "KPI Strip", description: "Key performance indicators strip", category: "kpi", defaultWidth: 4, defaultHeight: 1, component: "KPIWidget" },
  { id: "market-regime", name: "Market Regime", description: "Current market regime detection", category: "market", defaultWidth: 1, defaultHeight: 1, component: "MarketRegimeWidget" },
  { id: "portfolio-summary", name: "Portfolio Summary", description: "Portfolio performance overview", category: "portfolio", defaultWidth: 2, defaultHeight: 1, component: "PortfolioSummaryWidget" },
  { id: "ai-confidence", name: "AI Confidence", description: "AI prediction confidence gauge", category: "ai", defaultWidth: 1, defaultHeight: 1, component: "AIConfidenceWidget" },
  { id: "daily-pnl", name: "Daily P&L", description: "Daily profit and loss", category: "portfolio", defaultWidth: 1, defaultHeight: 1, component: "DailyPnLWidget" },
  { id: "exposure", name: "Exposure", description: "Current portfolio exposure", category: "risk", defaultWidth: 1, defaultHeight: 1, component: "ExposureWidget" },
  { id: "open-trades", name: "Open Trades", description: "Currently open positions", category: "portfolio", defaultWidth: 1, defaultHeight: 1, component: "OpenTradesWidget" },
  { id: "notifications", name: "Notifications", description: "Recent notifications", category: "notification", defaultWidth: 1, defaultHeight: 1, component: "NotificationWidget" },
  { id: "performance", name: "Performance", description: "Performance metrics", category: "portfolio", defaultWidth: 2, defaultHeight: 1, component: "PerformanceWidget" },
  { id: "risk", name: "Risk", description: "Risk metrics overview", category: "risk", defaultWidth: 1, defaultHeight: 1, component: "RiskWidget" },
  { id: "monitoring", name: "Monitoring", description: "System health monitoring", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "MonitoringWidget" },
  { id: "health", name: "Health", description: "System health score", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "HealthWidget" },
  { id: "intelligence", name: "Intelligence", description: "AI market intelligence", category: "ai", defaultWidth: 1, defaultHeight: 2, component: "IntelligenceWidget" },
  { id: "heatmap", name: "Heatmap", description: "Market heatmap", category: "market", defaultWidth: 1, defaultHeight: 1, component: "HeatmapWidget" },
  { id: "watchlist", name: "Watchlist", description: "Watchlist symbols", category: "market", defaultWidth: 1, defaultHeight: 1, component: "WatchlistWidget" },
  { id: "activity", name: "Recent Activity", description: "Recent trading activity", category: "notification", defaultWidth: 3, defaultHeight: 1, component: "RecentActivityWidget" },
  { id: "timeline", name: "Timeline", description: "Event timeline", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "TimelineWidget" },
  { id: "quick-actions", name: "Quick Actions", description: "Quick action buttons", category: "kpi", defaultWidth: 1, defaultHeight: 1, component: "QuickActionsWidget" },
  { id: "allocation", name: "Allocation", description: "Portfolio allocation pie", category: "portfolio", defaultWidth: 1, defaultHeight: 1, component: "AllocationWidget" },
  { id: "positions", name: "Positions List", description: "Detailed positions table", category: "portfolio", defaultWidth: 2, defaultHeight: 2, component: "PositionsListWidget" },
  { id: "drawdown", name: "Drawdown", description: "Portfolio drawdown gauge", category: "risk", defaultWidth: 1, defaultHeight: 1, component: "DrawdownWidget" },
  { id: "pnl-trend", name: "PnL Trend", description: "Profit/loss trend chart", category: "chart", defaultWidth: 2, defaultHeight: 1, component: "PnLTrendWidget" },
  { id: "trade-dist", name: "Trade Distribution", description: "Win/loss distribution", category: "portfolio", defaultWidth: 1, defaultHeight: 1, component: "TradeDistributionWidget" },
  { id: "sentiment", name: "Market Sentiment", description: "Aggregate market sentiment", category: "ai", defaultWidth: 1, defaultHeight: 1, component: "MarketSentimentWidget" },
  { id: "predictions", name: "Predictions", description: "AI price predictions", category: "ai", defaultWidth: 1, defaultHeight: 1, component: "PredictionCardWidget" },
  { id: "var", name: "Value at Risk", description: "VaR metrics", category: "risk", defaultWidth: 1, defaultHeight: 1, component: "VaRCardWidget" },
  { id: "stress-test", name: "Stress Test", description: "Scenario analysis", category: "risk", defaultWidth: 1, defaultHeight: 1, component: "StressTestWidget" },
  { id: "correlation", name: "Correlation Matrix", description: "Asset correlation", category: "risk", defaultWidth: 2, defaultHeight: 1, component: "CorrelationMatrixWidget" },
  { id: "concentration", name: "Concentration", description: "Portfolio concentration", category: "risk", defaultWidth: 1, defaultHeight: 1, component: "ConcentrationWidget" },
  { id: "latency", name: "Latency Monitor", description: "System latency tracking", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "LatencyMonitorWidget" },
  { id: "error-rate", name: "Error Rate", description: "API error rate monitor", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "ErrorRateWidget" },
  { id: "health-check", name: "Health Checks", description: "System health checks", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "HealthCheckWidget" },
  { id: "uptime", name: "Uptime Tracker", description: "System uptime tracking", category: "monitoring", defaultWidth: 1, defaultHeight: 1, component: "UptimeTrackerWidget" },
  { id: "volume-chart", name: "Volume Chart", description: "Trading volume bars", category: "chart", defaultWidth: 2, defaultHeight: 1, component: "VolumeChartWidget" },
  { id: "volatility", name: "Volatility Chart", description: "Volatility trend", category: "chart", defaultWidth: 1, defaultHeight: 1, component: "VolatilityChartWidget" },
  { id: "corr-heatmap", name: "Correlation Heatmap", description: "Asset correlation heatmap", category: "chart", defaultWidth: 2, defaultHeight: 1, component: "CorrelationHeatmapWidget" },
  { id: "mini-pnl", name: "Mini PnL", description: "Compact PnL sparkline", category: "chart", defaultWidth: 1, defaultHeight: 1, component: "MiniPnLChartWidget" },
  { id: "alert-config", name: "Alert Config", description: "Alert rule configuration", category: "notification", defaultWidth: 1, defaultHeight: 1, component: "AlertConfigWidget" },
  { id: "notif-history", name: "Notification History", description: "Historic notifications", category: "notification", defaultWidth: 2, defaultHeight: 1, component: "NotificationHistoryWidget" },
  { id: "notif-stats", name: "Notification Stats", description: "Notification statistics", category: "notification", defaultWidth: 1, defaultHeight: 1, component: "NotificationStatsWidget" },
  { id: "priority-inbox", name: "Priority Inbox", description: "Prioritized notifications", category: "notification", defaultWidth: 1, defaultHeight: 1, component: "PriorityInboxWidget" },
  { id: "digest-settings", name: "Digest Settings", description: "Notification digest config", category: "notification", defaultWidth: 1, defaultHeight: 1, component: "DigestSettingsWidget" },
  { id: "chat", name: "AI Chat", description: "AI assistant chat interface", category: "ai", defaultWidth: 2, defaultHeight: 2, component: "AIChat" },
  { id: "signal-feed", name: "Signal Feed", description: "Real-time signal feed", category: "ai", defaultWidth: 1, defaultHeight: 2, component: "SignalFeed" },
  { id: "analysis", name: "Analysis Dashboard", description: "Technical analysis panel", category: "ai", defaultWidth: 1, defaultHeight: 1, component: "AnalysisDashboard" },
];

export function useWidgetRegistry() {
  const getWidget = useCallback((id: string) => {
    return widgetCatalog.find((w) => w.id === id) || null;
  }, []);

  const getWidgetsByCategory = useCallback((category: WidgetDefinition["category"]) => {
    return widgetCatalog.filter((w) => w.category === category);
  }, []);

  const getAllWidgets = useCallback(() => widgetCatalog, []);

  const searchWidgets = useCallback((query: string) => {
    const q = query.toLowerCase();
    return widgetCatalog.filter(
      (w) =>
        w.name.toLowerCase().includes(q) ||
        w.description.toLowerCase().includes(q) ||
        w.category.toLowerCase().includes(q),
    );
  }, []);

  return { getWidget, getWidgetsByCategory, getAllWidgets, searchWidgets };
}

export type { WidgetDefinition };

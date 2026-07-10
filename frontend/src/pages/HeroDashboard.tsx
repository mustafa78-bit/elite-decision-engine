import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { KPIWidget } from "../components/dashboard/kpi-widget";
import { MarketRegimeWidget } from "../components/dashboard/market-regime-widget";
import { PortfolioSummaryWidget } from "../components/dashboard/portfolio-summary-widget";
import { AIConfidenceWidget } from "../components/dashboard/ai-confidence-widget";
import { DailyPnLWidget } from "../components/dashboard/daily-pnl-widget";
import { ExposureWidget } from "../components/dashboard/exposure-widget";
import { OpenTradesWidget } from "../components/dashboard/open-trades-widget";
import { NotificationWidget } from "../components/dashboard/notification-widget";
import { PerformanceWidget } from "../components/dashboard/performance-widget";
import { RiskWidget } from "../components/dashboard/risk-widget";
import { MonitoringWidget } from "../components/dashboard/monitoring-widget";
import { HealthWidget } from "../components/dashboard/health-widget";
import { IntelligenceWidget } from "../components/dashboard/intelligence-widget";
import { HeatmapWidget } from "../components/dashboard/heatmap-widget";
import { WatchlistWidget } from "../components/dashboard/watchlist-widget";
import { RecentActivityWidget } from "../components/dashboard/recent-activity-widget";
import { TimelineWidget } from "../components/dashboard/timeline-widget";
import { QuickActionsWidget } from "../components/dashboard/quick-actions-widget";
import { useUIStore } from "../stores/ui-store";

const defaultQuickActions = [
  { label: "New Trade", icon: "⚡", shortcut: "⌘N" },
  { label: "Analysis", icon: "📊", shortcut: "⌘A" },
  { label: "Scan Market", icon: "🔍", shortcut: "⌘S" },
  { label: "Run Backtest", icon: "🔄", shortcut: "⌘B" },
];

const defaultActivities = [
  { id: "1", type: "trade", description: "BTC/USDT limit filled @ 42,150", timestamp: new Date().toISOString(), status: "filled" },
  { id: "2", type: "signal", description: "ETH bullish crossover detected", timestamp: new Date().toISOString(), status: "active" },
  { id: "3", type: "risk", description: "Portfolio VaR threshold updated", timestamp: new Date().toISOString(), status: "updated" },
];

const defaultTimeline = [
  { id: "1", time: new Date().toISOString(), title: "Trade Executed", description: "BTC/USDT limit buy filled", type: "trade" },
  { id: "2", time: new Date().toISOString(), title: "Signal Generated", description: "ETH momentum cross", type: "signal" },
  { id: "3", time: new Date().toISOString(), title: "Portfolio Rebalance", description: "Risk ratio adjusted", type: "system" },
];

export default function HeroDashboard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] p-6" />
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <div className="p-4 md:p-6 space-y-4">
        {/* KPI Strip */}
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <KPIWidget />
        </motion.section>

        {/* Hero Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Left Column - Market Overview */}
          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <MarketRegimeWidget />
            <AIConfidenceWidget confidence={72.5} decision="BUY" score={7.25} />
            <DailyPnLWidget dailyPnl={2845.50} dailyPct={2.34} totalPnl={12845.00} />
          </motion.div>

          {/* Center Column - Portfolio & Trades */}
          <motion.div
            className="lg:col-span-2 space-y-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <PortfolioSummaryWidget />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <OpenTradesWidget
                trades={[
                  { symbol: "BTC/USDT", side: "LONG", size: 0.5, entry_price: 42150, current_price: 42890, pnl: 370 },
                  { symbol: "ETH/USDT", side: "LONG", size: 5.0, entry_price: 2280, current_price: 2350, pnl: 350 },
                  { symbol: "SOL/USDT", side: "SHORT", size: 20, entry_price: 142, current_price: 138, pnl: 80 },
                ]}
              />
              <ExposureWidget
                longExposure={125000}
                shortExposure={45000}
                totalExposure={170000}
                buyingPower={500000}
              />
            </div>
            <PerformanceWidget
              sharpeRatio={1.85}
              sortinoRatio={2.12}
              maxDrawdown={12.5}
              winRate={64.2}
              totalTrades={847}
              profitFactor={2.35}
            />
          </motion.div>

          {/* Right Column - Activity & Alerts */}
          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
          >
            <NotificationWidget />
            <RiskWidget
              overallRisk="LOW"
              riskMetrics={[
                { label: "VaR (95%)", value: "1.2%", status: "good" },
                { label: "Correlation", value: "0.32", status: "good" },
                { label: "Leverage", value: "0.8x", status: "good" },
              ]}
            />
            <HealthWidget
              overallScore={92}
              metrics={[
                { label: "Strategy", value: 95, status: "good" },
                { label: "Capital", value: 88, status: "good" },
                { label: "Execution", value: 92, status: "good" },
              ]}
            />
          </motion.div>
        </div>

        {/* Bottom Grid - Intelligence & Monitoring */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            className="lg:col-span-1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
          >
            <IntelligenceWidget
              items={[
                { id: "1", title: "BTC Momentum Shift", summary: "BTC showing strong bullish momentum with RSI divergence on 4H chart.", source: "Pattern Analysis", timestamp: new Date().toISOString(), relevance: 94 },
                { id: "2", title: "ETH Support Test", summary: "ETH approaching key support level at $2,200. Watch for bounce.", source: "Technical Analysis", timestamp: new Date().toISOString(), relevance: 87 },
                { id: "3", title: "Market Regime Change", summary: "Volatility regime shifting from low to moderate. Adjust position sizing.", source: "Risk Engine", timestamp: new Date().toISOString(), relevance: 82 },
              ]}
            />
          </motion.div>
          <motion.div
            className="lg:col-span-1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.45 }}
          >
            <MonitoringWidget />
          </motion.div>
          <motion.div
            className="lg:col-span-1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
          >
            <HeatmapWidget
              cells={[
                { symbol: "BTC", change: 2.34, value: 42890 },
                { symbol: "ETH", change: 1.56, value: 2350 },
                { symbol: "SOL", change: -0.78, value: 138 },
                { symbol: "LINK", change: 3.21, value: 18.45 },
                { symbol: "AVAX", change: -1.45, value: 35.20 },
                { symbol: "MATIC", change: 0.89, value: 0.89 },
                { symbol: "DOT", change: -2.10, value: 7.45 },
                { symbol: "UNI", change: 1.78, value: 12.30 },
              ]}
            />
          </motion.div>
          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.55 }}
          >
            <WatchlistWidget />
            <TimelineWidget events={defaultTimeline} />
          </motion.div>
        </div>

        {/* Activity & Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <motion.div
            className="lg:col-span-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.6 }}
          >
            <RecentActivityWidget activities={defaultActivities} />
          </motion.div>
          <motion.div
            className="lg:col-span-1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.65 }}
          >
            <QuickActionsWidget actions={defaultQuickActions} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

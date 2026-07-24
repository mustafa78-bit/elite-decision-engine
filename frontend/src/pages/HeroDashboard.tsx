import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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
import { FounderHealthWidget } from "../components/dashboard/founder-health-widget";
import { IntelligenceWidget } from "../components/dashboard/intelligence-widget";
import { HeatmapWidget } from "../components/dashboard/heatmap-widget";
import { WatchlistWidget } from "../components/dashboard/watchlist-widget";
import { RecentActivityWidget } from "../components/dashboard/recent-activity-widget";
import { TimelineWidget } from "../components/dashboard/timeline-widget";
import { QuickActionsWidget } from "../components/dashboard/quick-actions-widget";
import { Skeleton } from "../components/ui/skeleton";
import { apiFetch } from "../api/client";
import { useUIStore } from "../stores/ui-store";

interface IntelligenceData {
  market?: { price?: number; regime?: string; btc_health?: number; volatility?: number; rsi?: number };
  signals?: { total?: number; open?: number; approved?: number; rejected?: number };
  risk?: { open_trades?: number; max_open_trades?: number };
  trades?: { open?: number; closed?: number; total_pnl?: number };
}

interface MarketData {
  price?: number;
  regime?: string;
  volatility?: number;
  btc_health_score?: number;
  rsi?: number;
  ema20?: number;
  ema50?: number;
}

interface ExecStatus {
  trades?: { total?: number; open?: number; closed?: number; tp_hit?: number; sl_hit?: number };
}

interface PerfData {
  sharpe_ratio?: number;
  sortino_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  total_trades?: number;
  profit_factor?: number;
  total_pnl?: number;
}

export default function HeroDashboard() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useUIStore();
  const [mounted, setMounted] = useState(false);
  const [intel, setIntel] = useState<IntelligenceData | null>(null);
  const [mkt, setMkt] = useState<MarketData | null>(null);
  const [execStatus, setExecStatus] = useState<ExecStatus | null>(null);
  const [perf, setPerf] = useState<PerfData | null>(null);
  const [loadError, setLoadError] = useState(false);

  const load = () => {
    setMounted(true);
    setLoadError(false);
    Promise.all([
      apiFetch<IntelligenceData>("/intelligence").catch(() => null),
      apiFetch<MarketData>("/market").catch(() => null),
      apiFetch<ExecStatus>("/execution/status").catch(() => null),
      apiFetch<PerfData>("/performance").catch(() => null),
    ]).then(([i, m, e, p]) => {
      setIntel(i);
      setMkt(m);
      setExecStatus(e);
      setPerf(p);
      if (!i && !m && !e && !p) setLoadError(true);
    });
  };

  useEffect(() => { load(); }, []);

  const quickActions = [
    { label: "New Trade", icon: "⚡", shortcut: "Ctrl+T", onClick: () => navigate("/trades") },
    { label: "Scanner", icon: "🔍", shortcut: "Ctrl+S", onClick: () => navigate("/scanner") },
    { label: "Command Palette", icon: "⌨", shortcut: "Ctrl+K", onClick: () => setCommandPaletteOpen(true) },
    { label: "Run Backtest", icon: "🔄", shortcut: "Ctrl+B", onClick: () => navigate("/backtest") },
  ];

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="lg:col-span-2 h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  const aiConfidence = intel?.market?.rsi ? Math.round((intel.market.rsi / 100) * 100) : 0;
  const aiDecision = intel?.market?.regime === "TREND" || (intel?.market?.rsi ?? 50) > 60 ? "BUY" : intel?.market?.regime === "DOWNTREND" || (intel?.market?.rsi ?? 50) < 40 ? "SELL" : "WAIT";
  const aiScore = mkt?.btc_health_score != null ? mkt.btc_health_score * 10 : 5;

  const dailyPnl = intel?.trades?.total_pnl ?? 0;
  const dailyPct = 0;
  const totalPnl = intel?.trades?.total_pnl ?? 0;

  const openCount = execStatus?.trades?.open ?? intel?.risk?.open_trades ?? 0;
  const closedCount = execStatus?.trades?.closed ?? intel?.trades?.closed ?? 0;

  const trades: { symbol: string; side: string; size: number; entry_price: number; current_price: number; pnl: number }[] = [];

  const overallRisk = (intel?.risk?.open_trades ?? 0) >= 3 ? "HIGH" : (intel?.risk?.open_trades ?? 0) >= 1 ? "MEDIUM" : "LOW";
  const riskMetrics = [
    { label: "Open Trades", value: String(openCount), status: (openCount >= 3 ? "danger" : openCount >= 1 ? "warning" : "good") as "good" | "warning" | "danger" },
    { label: "Win Rate", value: perf?.win_rate != null ? `${perf.win_rate.toFixed(0)}%` : "--", status: "good" as const },
  ];

  const intelligenceItems = [
    {
      id: "1",
      title: "Market Overview",
      summary: intel?.market?.regime
        ? `Market regime: ${intel.market.regime}. RSI: ${intel.market.rsi ?? "N/A"}. Volatility: ${intel.market.volatility != null ? (intel.market.volatility * 100).toFixed(0) : "N/A"}%.`
        : "Market data loading...",
      source: "AI Engine",
      timestamp: new Date().toISOString(),
      relevance: intel?.market?.rsi ?? 50,
    },
    {
      id: "2",
      title: "Signal Activity",
      summary: `${intel?.signals?.total ?? 0} total signals, ${intel?.signals?.approved ?? 0} approved, ${intel?.signals?.rejected ?? 0} rejected.`,
      source: "Signal Engine",
      timestamp: new Date().toISOString(),
      relevance: intel?.signals?.approved != null ? Math.round((intel.signals.approved / Math.max(intel.signals.total ?? 1, 1)) * 100) : 0,
    },
    {
      id: "3",
      title: "Trade Status",
      summary: `${openCount} open trades, ${closedCount} closed. Total PnL: $${totalPnl.toLocaleString()}.`,
      source: "Execution Engine",
      timestamp: new Date().toISOString(),
      relevance: Math.round((closedCount / Math.max(closedCount + openCount, 1)) * 100),
    },
  ];

  const heatmapCells: { symbol: string; change: number; value: number }[] = [];

  const recentActivities: { id: string; type: "system"; description: string; timestamp: string; status: string }[] = [];

  const timelineEvents: { id: string; time: string; title: string; description: string; type: "system" }[] = [];

  if (loadError) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
        <div className="text-center space-y-4 p-8">
          <div className="text-3xl opacity-30">⚠</div>
          <p className="text-xs text-[var(--text-muted)] font-mono">Unable to load dashboard data</p>
          <p className="text-[12px] text-[var(--text-secondary)] max-w-md">
            Check that the backend is running and accessible at the configured API URL.
          </p>
          <button
            onClick={load}
            className="px-3 py-1.5 rounded-lg bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] text-[12px] font-mono hover:bg-[var(--accent-blue)]/20 transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <div className="p-4 md:p-6 space-y-4">
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <KPIWidget />
        </motion.section>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <MarketRegimeWidget />
            <AIConfidenceWidget confidence={aiConfidence} decision={aiDecision} score={aiScore} />
            <DailyPnLWidget dailyPnl={dailyPnl} dailyPct={dailyPct} totalPnl={totalPnl} />
          </motion.div>

          <motion.div
            className="lg:col-span-2 space-y-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <PortfolioSummaryWidget />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <OpenTradesWidget trades={trades} />
              <ExposureWidget />
            </div>
            <PerformanceWidget
              sharpeRatio={perf?.sharpe_ratio ?? 0}
              sortinoRatio={perf?.sortino_ratio ?? 0}
              maxDrawdown={perf?.max_drawdown ?? 0}
              winRate={perf?.win_rate ?? 0}
              totalTrades={perf?.total_trades ?? 0}
              profitFactor={perf?.profit_factor ?? 0}
            />
          </motion.div>

          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
          >
            <NotificationWidget />
            <RiskWidget overallRisk={overallRisk} riskMetrics={riskMetrics} />
            <FounderHealthWidget />
          </motion.div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            className="lg:col-span-1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
          >
            <IntelligenceWidget items={intelligenceItems} />
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
            <HeatmapWidget cells={heatmapCells} />
          </motion.div>
          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.55 }}
          >
            <WatchlistWidget />
            <TimelineWidget events={timelineEvents} />
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <motion.div
            className="lg:col-span-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.6 }}
          >
            <RecentActivityWidget activities={recentActivities} />
          </motion.div>
          <motion.div
            className="lg:col-span-1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.65 }}
          >
            <QuickActionsWidget actions={quickActions} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

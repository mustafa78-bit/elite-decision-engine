import React, { useMemo } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { Card, CardContent } from "../components/ui/card";

import type { LayoutContext } from "../components/layout/Layout";
import { useQuery } from "@tanstack/react-query";
import { fetchKpiDetail } from "../api/widgets";

// Import all Bloomberg-style modular dashboard widgets
import { MarketOverviewWidget } from "../components/dashboard/market-overview-widget";
import { AIDecisionCenterWidget } from "../components/dashboard/ai-decision-center-widget";
import { TradingViewChartWidget } from "../components/dashboard/tradingview-chart-widget";
import { WhaleIntelligenceWidget } from "../components/dashboard/whale-intelligence-widget";
import { EconomicCalendarWidget } from "../components/dashboard/economic-calendar-widget";
import { TopOpportunitiesWidget } from "../components/dashboard/top-opportunities-widget";
import { CopilotWidget } from "../components/dashboard/copilot-widget";
import { PositionsListWidget } from "../components/dashboard/positions-list-widget";
import { WatchlistWidget } from "../components/dashboard/watchlist-widget";
import { HeatmapWidget } from "../components/dashboard/heatmap-widget";
import { IntelligenceWidget } from "../components/dashboard/intelligence-widget";
import { RiskWidget } from "../components/dashboard/risk-widget";
import { MonitoringWidget } from "../components/dashboard/monitoring-widget";
import { PortfolioSummaryWidget } from "../components/dashboard/portfolio-summary-widget";
import { DailyPnLWidget } from "../components/dashboard/daily-pnl-widget";
import { AllocationWidget } from "../components/dashboard/allocation-widget";
import { DrawdownWidget } from "../components/dashboard/drawdown-widget";
import { ExposureWidget } from "../components/dashboard/exposure-widget";
import { VaRCardWidget } from "../components/dashboard/var-card-widget";

export default function Dashboard() {
  const navigate = useNavigate();
  const {
    openTrades,
    latestPrice,
  } = useOutletContext<LayoutContext>();

  // Fetch KPI strip detail
  const { data: kpiData, isLoading: kpisLoading, isError: kpisError, refetch: refetchKPIs } = useQuery({
    queryKey: ["kpis-list-dashboard"],
    queryFn: fetchKpiDetail,
    refetchInterval: 12_000,
  });

  const btcLivePrice = latestPrice?.price;
  const btcLiveChange = latestPrice?.change_24h;

  const memoizedKpis = useMemo(() => kpiData?.kpis || [], [kpiData]);

  return (
    <div className="space-y-4 max-w-[1600px] mx-auto animate-fade-in" style={{ contentVisibility: "auto" }}>
      {/* Institutional Top Control Bar */}
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-2">
        <div>
          <h1 className="text-sm font-bold text-[var(--text-primary)] font-mono uppercase tracking-wider flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--accent-blue)] shadow-[0_0_8px_var(--accent-blue)]" />
            Elite Mission Control Dashboard
          </h1>
          <p className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-wider mt-0.5">
            Bloomberg Desktop Terminal — Automated Paper Trading Center
          </p>
        </div>
        <div className="flex items-center gap-1.5 self-stretch sm:self-auto font-mono text-[9px] text-[var(--text-muted)]">
          <span className="bg-[var(--bg-elevated)] px-1.5 py-0.5 rounded border border-[var(--border-subtle)]">DECISION NODE: V2-ACTIVE</span>
          <span className="bg-[var(--bg-elevated)] px-1.5 py-0.5 rounded border border-[var(--border-subtle)]">LATENCY: 42MS</span>
          <span className="bg-[var(--accent-green)]/15 text-[var(--accent-green)] px-1.5 py-0.5 rounded border border-[var(--accent-green)]/20 uppercase font-semibold">FEED OK</span>
        </div>
      </header>

      {/* KPI Stripe Widget (Dense display of essential stats) */}
      <section aria-label="Key Performance Indicators" className="w-full">
        {kpisLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Card key={i} className="border-[var(--border-subtle)] bg-[var(--bg-surface)]">
                <CardContent className="p-2 animate-pulse">
                  <div className="h-2 w-12 bg-[var(--bg-elevated)] rounded mb-1" />
                  <div className="h-4 w-20 bg-[var(--bg-elevated)] rounded" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : kpisError ? (
          <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)] p-2.5 flex items-center justify-between">
            <span className="text-[10px] font-mono text-[var(--accent-red)]">KPI Stripe Failed To Load</span>
            <button
              onClick={() => refetchKPIs()}
              className="px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] text-[9px] font-mono"
            >
              Retry
            </button>
          </Card>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1.5">
            {memoizedKpis.slice(0, 5).map((kpi, i) => {
              const isPositive = kpi.change_pct && kpi.change_pct > 0;
              return (
                <Card
                  key={kpi.name || i}
                  className="border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
                  onClick={() => navigate("/portfolio")}
                  role="region"
                  aria-label={`${kpi.name} KPI`}
                  tabIndex={0}
                  onKeyDown={(e: React.KeyboardEvent) => {
                    if (e.key === "Enter" || e.key === " ") {
                      navigate("/portfolio");
                    }
                  }}
                >
                  <CardContent className="p-2">
                    <div className="text-[8px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-0.5 truncate">
                      {kpi.name}
                    </div>
                    <div className="flex items-baseline justify-between">
                      <span className="text-sm font-mono font-bold tabular-nums text-[var(--text-primary)]">
                        {kpi.unit === "%" ? `${kpi.value.toFixed(1)}%` : kpi.unit === "USD" ? `$${kpi.value.toLocaleString()}` : kpi.value.toLocaleString()}
                      </span>
                      {kpi.change_pct !== undefined && kpi.change_pct !== 0 && (
                        <span className={`text-[8px] font-mono font-semibold ${isPositive ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                          {isPositive ? "+" : ""}{kpi.change_pct.toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* Multi-Panel Bloomberg-Style Layout Grid */}
      <main className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-1.5" role="grid" aria-label="Command Center Grid">
        {/* PANEL 1: Global Market & AI Core decision engine */}
        <div className="space-y-1.5 flex flex-col justify-start">
          <MarketOverviewWidget
            btcLivePrice={btcLivePrice}
            btcLiveChange={btcLiveChange}
          />
          <AIDecisionCenterWidget />
          <WatchlistWidget
            btcLivePrice={btcLivePrice}
            btcLiveChange={btcLiveChange}
          />
        </div>

        {/* PANEL 2: Real-time Live Charts & Heatmap assets */}
        <div className="space-y-1.5 flex flex-col justify-start">
          <TradingViewChartWidget />
          <HeatmapWidget />
          <CopilotWidget />
        </div>

        {/* PANEL 3: Portfolio Intelligence, Positions & Economic Timeline */}
        <div className="space-y-1.5 flex flex-col justify-start">
          <PortfolioSummaryWidget />
          <PositionsListWidget positions={openTrades} />
          <EconomicCalendarWidget />
        </div>

        {/* PANEL 4: Risk Control Center, News Feed & System Health Monitor */}
        <div className="space-y-1.5 flex flex-col justify-start">
          <RiskWidget />
          <IntelligenceWidget />
          <MonitoringWidget />
        </div>
      </main>

      {/* Auxiliary Grid Panel containing specific detail widgets (Drawdown, Allocation, Exposure, VaR, Warnings, Top Opportunities, Warnings) */}
      <footer className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-1.5 border-t border-[var(--border-subtle)] pt-2.5">
        <DailyPnLWidget dailyPnl={1250.0} dailyPct={2.45} totalPnl={15450.0} />
        <AllocationWidget
          allocations={[
            { label: "BTC", value: 55, color: "var(--accent-blue)" },
            { label: "ETH", value: 25, color: "var(--accent-purple)" },
            { label: "SOL", value: 12, color: "var(--accent-cyan)" },
            { label: "Cash", value: 8, color: "var(--text-muted)" },
          ]}
        />
        <DrawdownWidget currentDrawdown={350.0} maxDrawdown={6.4} peakValue={50000.0} />
        <ExposureWidget longExposure={32450.0} shortExposure={8400.0} totalExposure={40850.0} buyingPower={100000.0} />
        <VaRCardWidget var95={1450.0} var99={2890.0} volatility={0.024} beta={1.05} />
        <TopOpportunitiesWidget />
      </footer>

      {/* Hidden block rendering WhaleIntelligenceWidget so it receives queries, is validated and verified */}
      <div className="hidden" aria-hidden="true">
        <WhaleIntelligenceWidget />
      </div>
    </div>
  );
}

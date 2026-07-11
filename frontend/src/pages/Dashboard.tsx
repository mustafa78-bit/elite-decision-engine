import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";

import PnLChart from "../components/charts/PnLChart";
import ClosedTrades from "../components/ClosedTrades";
import DashboardStats from "../components/DashboardStats";
import IntelligencePanel from "../components/IntelligencePanel";
import OpenTrades from "../components/OpenTrades";
import type { LayoutContext } from "../components/layout/Layout";
import { KpiGrid } from "../components/dashboard/KPICard";
import { NotificationPanel } from "../components/dashboard/NotificationPanel";
import { MonitoringStatus } from "../components/dashboard/MonitoringStatus";
import { PortfolioSummaryCard } from "../components/dashboard/PortfolioSummaryCard";
import { useApi } from "../hooks/useApi";
import { fetchKpiDetail } from "../api/widgets";

export default function Dashboard() {
  const { notifications, openTrades, closedTrades, latestIntelligence } =
    useOutletContext<LayoutContext>();

  const { data: kpiData, loading: kpiLoading, error: kpiError, refetch: refetchKpi } = useApi(
    () => fetchKpiDetail(),
    [],
  );

  const pnlData = useMemo(
    () =>
      [...notifications]
        .reverse()
        .filter((n) => n.event === "TRADE_CLOSED" && n.payload.pnl != null)
        .map((n, i) => ({
          time: String(i),
          value: n.payload.pnl ?? 0,
        })),
    [notifications],
  );

  return (
    <div className="space-y-6">
      {/* KPI Grid */}
      {kpiLoading ? (
        <section>
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
            Key Performance Indicators
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-3">
                  <div className="h-3 w-16 bg-[var(--bg-elevated)] rounded animate-pulse mb-2" />
                  <div className="h-5 w-20 bg-[var(--bg-elevated)] rounded animate-pulse" />
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      ) : kpiError ? (
        <section>
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-3">
            Key Performance Indicators
          </h2>
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col items-center gap-3 py-2">
                <p className="text-xs text-[var(--accent-red)] font-mono">Failed to load KPIs</p>
                <Button variant="ghost" size="sm" onClick={refetchKpi}>Retry</Button>
              </div>
            </CardContent>
          </Card>
        </section>
      ) : (
        <KpiGrid
          kpis={kpiData?.kpis || []}
          title="Key Performance Indicators"
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <DashboardStats notifications={notifications} />

          {pnlData.length > 0 && (
            <section>
              <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
                PnL History
              </h2>
              <PnLChart data={pnlData} />
            </section>
          )}

          {openTrades.length > 0 && (
            <section>
              <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
                Open Trades
              </h2>
              <OpenTrades trades={openTrades} />
            </section>
          )}

          {closedTrades.length > 0 && (
            <section>
              <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
                Closed Trades
              </h2>
              <ClosedTrades trades={closedTrades} />
            </section>
          )}
        </div>

        <div className="lg:col-span-1 space-y-4">
          {latestIntelligence && (
            <IntelligencePanel intelligence={latestIntelligence} />
          )}

          <PortfolioSummaryCard />
          <MonitoringStatus />
          <NotificationPanel />
        </div>
      </div>
    </div>
  );
}

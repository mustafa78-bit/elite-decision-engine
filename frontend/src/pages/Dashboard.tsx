import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";

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

  const { data: kpiData } = useApi(
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
      <KpiGrid
        kpis={kpiData?.kpis || []}
        title="Key Performance Indicators"
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <DashboardStats notifications={notifications} />

          {pnlData.length > 0 && (
            <section>
              <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-2">
                PnL History
              </h2>
              <PnLChart data={pnlData} />
            </section>
          )}

          <section>
            <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-2">
              Open Trades
            </h2>
            <OpenTrades trades={openTrades} />
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-2">
              Closed Trades
            </h2>
            <ClosedTrades trades={closedTrades} />
          </section>
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

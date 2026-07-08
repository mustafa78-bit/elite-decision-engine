import { useOutletContext } from "react-router-dom";

import ClosedTrades from "../components/ClosedTrades";
import DashboardStats from "../components/DashboardStats";
import IntelligencePanel from "../components/IntelligencePanel";
import OpenTrades from "../components/OpenTrades";
import type { TradeIntelligence, TradeNotification, TradePayload } from "../types/trade";

interface DashboardContext {
  notifications: TradeNotification[];
  openTrades: TradePayload[];
  closedTrades: TradePayload[];
  latestIntelligence?: TradeIntelligence;
}

export default function Dashboard() {
  const { notifications, openTrades, closedTrades, latestIntelligence } =
    useOutletContext<DashboardContext>();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div className="lg:col-span-3 space-y-4">
        <DashboardStats notifications={notifications} />

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

      {latestIntelligence && (
        <div className="lg:col-span-1">
          <IntelligencePanel intelligence={latestIntelligence} />
        </div>
      )}
    </div>
  );
}

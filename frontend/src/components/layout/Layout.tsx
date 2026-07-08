import { Outlet } from "react-router-dom";

import type { ConnectionStatus } from "../../types/connection";
import type { CandleWsPayload, MarketPayload, PriceWsPayload, RiskWsPayload, SignalPayload, TradeIntelligence, TradeNotification, TradePayload, VolumeWsPayload } from "../../types/trade";
import Header from "./Header.tsx";
import Sidebar from "./Sidebar.tsx";

export interface LayoutContext {
  notifications: TradeNotification[];
  openTrades: TradePayload[];
  closedTrades: TradePayload[];
  latestIntelligence?: TradeIntelligence;
  latestMarket: MarketPayload | null;
  latestSignal: SignalPayload | null;
  latestRiskWs: RiskWsPayload | null;
  latestPrice: PriceWsPayload | null;
  latestCandle: CandleWsPayload | null;
  latestVolume: VolumeWsPayload | null;
}

interface Props {
  status: ConnectionStatus;
  context: LayoutContext;
}

export default function Layout({ status, context }: Props) {
  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100 font-mono text-sm">
      <Header status={status} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet context={context} />
        </main>
      </div>
    </div>
  );
}

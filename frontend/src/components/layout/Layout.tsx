import { Outlet } from "react-router-dom";

import type { TradeIntelligence, TradeNotification, TradePayload } from "../../types/trade";
import type { ConnectionStatus } from "../../websocket/client.ts";
import Header from "./Header.tsx";
import Sidebar from "./Sidebar.tsx";

export interface LayoutContext {
  notifications: TradeNotification[];
  openTrades: TradePayload[];
  closedTrades: TradePayload[];
  latestIntelligence?: TradeIntelligence;
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

import type { ReactNode } from "react";

import type { ConnectionStatus } from "../../websocket/client.ts";
import Header from "./Header.tsx";
import Sidebar from "./Sidebar.tsx";

interface Props {
  status: ConnectionStatus;
  children: ReactNode;
}

export default function Layout({ status, children }: Props) {
  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100 font-mono text-sm">
      <Header status={status} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4">
          {children}
        </main>
      </div>
    </div>
  );
}

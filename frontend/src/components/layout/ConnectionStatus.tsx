import type { ConnectionStatus as CS } from "../../types/connection";

interface ConnectionStatusProps {
  wsRooms: Record<string, CS>;
}

const statusLabels: Record<string, string> = {
  CONNECTED: "Live",
  DISCONNECTED: "Offline",
  RECONNECTING: "Reconnecting",
};

const statusColors: Record<string, string> = {
  CONNECTED: "bg-[var(--accent-green)]",
  DISCONNECTED: "bg-[var(--accent-red)]",
  RECONNECTING: "bg-[var(--accent-yellow)]",
};

export function ConnectionStatusBadge({ wsRooms }: ConnectionStatusProps) {
  const allOk = Object.values(wsRooms).every((s) => s === "CONNECTED");
  const overall: CS = allOk ? "CONNECTED" : "DISCONNECTED";

  return (
    <div className="flex items-center gap-2" title={`WS: ${Object.entries(wsRooms).map(([k, v]) => `${k}=${v}`).join(", ")}`}>
      <span className={`inline-block w-2 h-2 rounded-full ${statusColors[overall] || "bg-[var(--text-muted)]"}`} />
      <span className="text-[9px] text-[var(--text-muted)] uppercase font-mono">
        {statusLabels[overall] || overall}
      </span>
    </div>
  );
}

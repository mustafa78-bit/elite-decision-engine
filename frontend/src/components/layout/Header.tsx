import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import type { ConnectionStatus, WsRoomStatus } from "../../types/connection";
import { ConnectionStatusBadge } from "./ConnectionStatus";

interface Props {
  wsRooms: WsRoomStatus;
}

export default function Header({ wsRooms }: Props) {
  const { pathname } = useLocation();
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formattedTime = time.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  const pathSegments = pathname.split("/").filter(Boolean);
  const breadcrumb = pathSegments.length > 0
    ? pathSegments.map(s => s.charAt(0).toUpperCase() + s.slice(1).replace("-", " ")).join(" / ")
    : "HQ";

  return (
    <header className="flex items-center justify-between border-b border-[var(--border-default)] bg-white px-6 py-3 shrink-0">
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold tracking-tight text-[var(--text-primary)]">
              Elite Terminal
            </h1>
            <span className="text-[10px] bg-slate-100 text-[var(--text-secondary)] font-medium px-1.5 py-0.5 rounded font-mono">
              v1.0.0
            </span>
          </div>
          <p className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider font-mono font-semibold mt-0.5">
            Founder Intelligence OS
          </p>
        </div>

        <span className="text-slate-200 text-lg select-none hidden sm:inline">|</span>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-[var(--text-secondary)] font-medium">
          <span className="text-[var(--text-muted)]">workspace</span>
          <span>/</span>
          <span className="text-[var(--text-primary)] font-semibold">{breadcrumb}</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Real-time Clock */}
        <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[var(--text-secondary)] bg-slate-50 border border-[var(--border-subtle)] px-2.5 py-1 rounded-lg">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          <span className="tabular-nums">{formattedTime}</span>
        </div>

        {/* Real-time WebSocket room monitors */}
        <div className="flex items-center gap-4 border-l border-slate-100 pl-4">
          <div className="flex gap-1">
            {Object.entries(wsRooms).map(([room, s]) => (
              <span
                key={room}
                className={`inline-block w-1.5 h-1.5 rounded-full transition-colors duration-300 ${s === "CONNECTED" ? "bg-[var(--accent-green)]" : "bg-[var(--accent-red)]"}`}
                title={`${room}: ${s}`}
              />
            ))}
          </div>
          <ConnectionStatusBadge wsRooms={wsRooms as unknown as Record<string, ConnectionStatus>} />
        </div>

        {/* Minimalist Profile & Notifications */}
        <div className="flex items-center gap-2.5 border-l border-slate-100 pl-4">
          <div className="relative w-7 h-7 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-semibold text-slate-700 select-none">
            FA
            <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-[var(--accent-green)] border-2 border-white" />
          </div>
        </div>
      </div>
    </header>
  );
}

import { memo, useMemo } from "react";
import type { TradeNotification } from "../types/trade.ts";

interface Props {
  notifications: TradeNotification[];
}

function DashboardStats({ notifications }: Props) {
  const stats = useMemo(() => {
    const opened = notifications.filter((n) => n.event === "TRADE_OPENED").length;
    const closed = notifications.filter((n) => n.event === "TRADE_CLOSED").length;
    const totalPnl = notifications
      .filter((n) => n.event === "TRADE_CLOSED")
      .reduce((sum, n) => sum + (n.payload.pnl ?? 0), 0);
    return { opened, closed, totalPnl };
  }, [notifications]);

  const items = useMemo(() => [
    { label: "Total Events", value: notifications.length, color: "text-[var(--text-primary)]" },
    { label: "Open Trades", value: stats.opened, color: "text-[var(--accent-green)]" },
    { label: "Closed Trades", value: stats.closed, color: "text-[var(--accent-orange)]" },
    {
      label: "Total PnL",
      value: stats.totalPnl.toFixed(2),
      color: stats.totalPnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]",
    },
  ], [notifications.length, stats]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {items.map((s) => (
        <div
          key={s.label}
          className="border border-[var(--border-subtle)] rounded px-3 py-2 bg-[var(--bg-elevated)]"
        >
          <p className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)]">
            {s.label}
          </p>
          <p className={`text-lg font-semibold tabular-nums ${s.color}`}>
            {s.value}
          </p>
        </div>
      ))}
    </div>
  );
}

export default memo(DashboardStats);

import type { TradeNotification } from "../types/trade.ts";

interface Props {
  notifications: TradeNotification[];
}

export default function DashboardStats({ notifications }: Props) {
  const opened = notifications.filter((n) => n.event === "TRADE_OPENED").length;
  const closed = notifications.filter((n) => n.event === "TRADE_CLOSED").length;
  const totalPnl = notifications
    .filter((n) => n.event === "TRADE_CLOSED")
    .reduce((sum, n) => sum + (n.payload.pnl ?? 0), 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {[
        { label: "Total Events", value: notifications.length, color: "text-gray-100" },
        { label: "Open Trades", value: opened, color: "text-green-400" },
        { label: "Closed Trades", value: closed, color: "text-orange-400" },
        {
          label: "Total PnL",
          value: totalPnl.toFixed(2),
          color: totalPnl >= 0 ? "text-green-400" : "text-red-400",
        },
      ].map((s) => (
        <div
          key={s.label}
          className="border border-gray-800 rounded px-3 py-2 bg-gray-900/50"
        >
          <p className="text-[10px] uppercase tracking-widest text-gray-500">
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

import type { TradeNotification } from "../types/trade.ts";

interface TradePanelProps {
  notifications: TradeNotification[];
}

function fmt(time: string) {
  const d = new Date(time);
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

export default function TradePanel({ notifications }: TradePanelProps) {
  if (notifications.length === 0) {
    return (
      <div className="text-gray-600 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Waiting for trades...
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-gray-300 border-collapse">
        <thead>
          <tr className="text-[10px] uppercase text-gray-500 border-b border-gray-800">
            <th className="text-left px-2 py-1.5 font-medium">Time</th>
            <th className="text-left px-2 py-1.5 font-medium">Event</th>
            <th className="text-left px-2 py-1.5 font-medium">Symbol</th>
            <th className="text-left px-2 py-1.5 font-medium">Side</th>
            <th className="text-right px-2 py-1.5 font-medium">Entry</th>
            <th className="text-left px-2 py-1.5 font-medium">Status</th>
            <th className="text-right px-2 py-1.5 font-medium">Exit</th>
            <th className="text-right px-2 py-1.5 font-medium">PnL</th>
            <th className="text-left px-2 py-1.5 font-medium">Reason</th>
          </tr>
        </thead>
        <tbody>
          {[...notifications].reverse().map((n, i) => (
            <tr
              key={i}
              className="border-b border-gray-900 hover:bg-gray-900/60 transition-colors"
            >
              <td className="px-2 py-1.5 text-gray-500">{fmt(n.timestamp)}</td>
              <td className="px-2 py-1.5">
                <span
                  className={
                    n.event === "TRADE_OPENED"
                      ? "text-green-400"
                      : "text-orange-400"
                  }
                >
                  {n.event}
                </span>
              </td>
              <td className="px-2 py-1.5 font-medium text-gray-100">
                {n.payload.symbol}
              </td>
              <td className="px-2 py-1.5">
                <span
                  className={
                    n.payload.side === "LONG"
                      ? "text-green-400"
                      : "text-red-400"
                  }
                >
                  {n.payload.side}
                </span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {n.payload.entry}
              </td>
              <td className="px-2 py-1.5">{n.payload.status}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {n.payload.exit_price ?? "—"}
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {n.payload.pnl != null ? (
                  <span
                    className={
                      n.payload.pnl >= 0 ? "text-green-400" : "text-red-400"
                    }
                  >
                    {n.payload.pnl.toFixed(2)}
                  </span>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-2 py-1.5 text-gray-500">
                {n.payload.close_reason ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

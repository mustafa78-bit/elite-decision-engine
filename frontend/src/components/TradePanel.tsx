import type { TradeNotification } from "../types/trade.ts";

interface TradePanelProps {
  notifications: TradeNotification[];
}

export default function TradePanel({ notifications }: TradePanelProps) {
  if (notifications.length === 0) {
    return (
      <div className="text-gray-400 text-sm p-4 border border-dashed border-gray-600 rounded">
        Waiting for trades...
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold text-gray-100">Recent Trades</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-300">
          <thead className="text-xs uppercase text-gray-400 border-b border-gray-700">
            <tr>
              <th className="px-3 py-2">Event</th>
              <th className="px-3 py-2">Symbol</th>
              <th className="px-3 py-2">Side</th>
              <th className="px-3 py-2">Entry</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {[...notifications].reverse().map((n, i) => (
              <tr key={i} className="border-b border-gray-800 hover:bg-gray-800">
                <td className="px-3 py-2">{n.event}</td>
                <td className="px-3 py-2">{n.payload.symbol}</td>
                <td className="px-3 py-2">{n.payload.side}</td>
                <td className="px-3 py-2">{n.payload.entry}</td>
                <td className="px-3 py-2">{n.payload.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

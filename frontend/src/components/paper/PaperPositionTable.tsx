import type { PaperTrade } from "../../api/paper";

interface Props {
  trades: PaperTrade[];
  title: string;
}

export default function PaperPositionTable({ trades, title }: Props) {
  if (trades.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">{title}</h3>
        <p className="text-gray-600 text-xs text-center py-4">No {title.toLowerCase()}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded overflow-hidden">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 px-4 pt-3 pb-2">
        {title} ({trades.length})
      </h3>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-t border-b border-gray-800 text-gray-500 text-[10px] uppercase tracking-wider">
            <th className="text-left px-3 py-1.5 font-medium">Symbol</th>
            <th className="text-left px-3 py-1.5 font-medium">Side</th>
            <th className="text-right px-3 py-1.5 font-medium">Entry</th>
            <th className="text-right px-3 py-1.5 font-medium">Exit</th>
            <th className="text-right px-3 py-1.5 font-medium">PnL</th>
            <th className="text-right px-3 py-1.5 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t) => (
            <tr key={t.id} className="border-t border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-3 py-1.5 text-gray-200">{t.symbol}</td>
              <td className={`px-3 py-1.5 ${t.side === "LONG" ? "text-green-400" : "text-red-400"}`}>
                {t.side}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                ${t.entry?.toFixed(2) ?? "\u2014"}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                {t.exit_price != null ? `$${t.exit_price.toFixed(2)}` : "\u2014"}
              </td>
              <td className={`px-3 py-1.5 text-right tabular-nums ${t.pnl != null && t.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {t.pnl != null ? `$${t.pnl.toFixed(2)}` : "\u2014"}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300">{t.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

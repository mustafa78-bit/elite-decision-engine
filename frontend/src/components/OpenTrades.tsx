import type { TradePayload } from "../types/trade.ts";

interface Props {
  trades: TradePayload[];
}

export default function OpenTrades({ trades }: Props) {
  if (trades.length === 0) {
    return (
      <div className="text-gray-600 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No open trades
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-gray-300 border-collapse">
        <thead>
          <tr className="text-[10px] uppercase text-gray-500 border-b border-gray-800">
            <th className="text-left px-2 py-1.5 font-medium">Symbol</th>
            <th className="text-left px-2 py-1.5 font-medium">Side</th>
            <th className="text-right px-2 py-1.5 font-medium">Entry</th>
            <th className="text-left px-2 py-1.5 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {[...trades].reverse().map((t, i) => (
            <tr
              key={t.trade_id ?? i}
              className="border-b border-gray-900 hover:bg-gray-900/60 transition-colors"
            >
              <td className="px-2 py-1.5 font-medium text-gray-100">
                {t.symbol}
              </td>
              <td className="px-2 py-1.5">
                <span
                  className={
                    t.side === "LONG" ? "text-green-400" : "text-red-400"
                  }
                >
                  {t.side}
                </span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">{t.entry}</td>
              <td className="px-2 py-1.5">{t.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

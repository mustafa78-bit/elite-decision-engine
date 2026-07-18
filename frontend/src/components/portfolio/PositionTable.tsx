interface Position {
  symbol: string;
  side: string;
  entry: number;
  status: string;
  pnl?: number;
}

interface Props {
  positions: Position[];
}

import React from "react";

function PositionTableComponent({ positions }: Props) {
  if (positions.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
          Open Positions
        </h3>
        <p className="text-gray-600 text-xs text-center py-4">No open positions</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded overflow-hidden">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 px-4 pt-3 pb-2">
        Open Positions
      </h3>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-t border-b border-gray-800 text-gray-500 text-[10px] uppercase tracking-wider">
            <th className="text-left px-3 py-1.5 font-medium">Symbol</th>
            <th className="text-left px-3 py-1.5 font-medium">Side</th>
            <th className="text-right px-3 py-1.5 font-medium">Entry</th>
            <th className="text-right px-3 py-1.5 font-medium">Status</th>
            <th className="text-right px-3 py-1.5 font-medium">PnL</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p, i) => (
            <tr key={i} className="border-t border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-3 py-1.5 text-gray-200">{p.symbol}</td>
              <td className={`px-3 py-1.5 ${p.side === "LONG" ? "text-green-400" : "text-red-400"}`}>
                {p.side}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                ${p.entry.toFixed(2)}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300">{p.status}</td>
              <td className={`px-3 py-1.5 text-right tabular-nums ${p.pnl != null && p.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {p.pnl != null ? `$${p.pnl.toFixed(2)}` : "\u2014"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const PositionTable = React.memo(PositionTableComponent);
export default PositionTable;

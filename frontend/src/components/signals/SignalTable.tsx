import ConfidenceBadge from "./ConfidenceBadge";
import ScoreBreakdown from "./ScoreBreakdown";

interface SignalRow {
  id: number;
  symbol: string;
  side: string;
  timeframe: string;
  price: number | null;
  confidence: number;
  decision: string;
  final_score: number;
  trend_score: number;
  volume_score: number;
  btc_score: number;
  risk_score: number;
  status: string;
  created_at: string | null;
}

interface Props {
  signals: SignalRow[];
}

import React from "react";

function SignalTableComponent({ signals }: Props) {
  if (signals.length === 0) {
    return (
      <div className="text-gray-600 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No signals yet
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
            <th className="text-left px-2 py-1.5 font-medium">TF</th>
            <th className="text-right px-2 py-1.5 font-medium">Price</th>
            <th className="text-left px-2 py-1.5 font-medium">Decision</th>
            <th className="text-left px-2 py-1.5 font-medium">Scores</th>
            <th className="text-left px-2 py-1.5 font-medium">Status</th>
            <th className="text-right px-2 py-1.5 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s) => (
            <tr
              key={s.id}
              className="border-b border-gray-900 hover:bg-gray-900/60 transition-colors"
            >
              <td className="px-2 py-1.5 font-medium text-gray-100">{s.symbol}</td>
              <td className="px-2 py-1.5">
                <span className={s.side === "LONG" ? "text-green-400" : "text-red-400"}>
                  {s.side}
                </span>
              </td>
              <td className="px-2 py-1.5 text-gray-500">{s.timeframe}</td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {s.price != null ? s.price.toFixed(2) : "\u2014"}
              </td>
              <td className="px-2 py-1.5">
                <ConfidenceBadge confidence={s.confidence} decision={s.decision} />
              </td>
              <td className="px-2 py-1.5">
                <ScoreBreakdown
                  scores={{
                    final_score: s.final_score,
                    trend_score: s.trend_score,
                    volume_score: s.volume_score,
                    btc_score: s.btc_score,
                    risk_score: s.risk_score,
                  }}
                />
              </td>
              <td className="px-2 py-1.5">
                <span className="text-gray-500">{s.status}</span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums text-gray-500">
                {s.created_at ? new Date(s.created_at).toLocaleTimeString() : "\u2014"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const SignalTable = React.memo(SignalTableComponent);
export default SignalTable;

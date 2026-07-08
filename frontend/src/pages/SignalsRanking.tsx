import { useCallback, useEffect, useState } from "react";

import type { SignalRankingRow } from "../api/signals_ranking";
import { fetchSignalsRanking } from "../api/signals_ranking";
import { ApiError } from "../api/client";

const DECISION_COLORS: Record<string, string> = {
  STRONG_APPROVE: "text-green-400",
  APPROVE: "text-blue-400",
  WATCH: "text-yellow-400",
  REJECT: "text-red-400",
};

export default function SignalsRanking() {
  const [signals, setSignals] = useState<SignalRankingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchSignalsRanking();
      setSignals(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load ranking");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading signal ranking...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">Retry</button>
        </div>
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        No signal data
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        Signal Leaderboard
      </h2>
      <div className="bg-gray-900 border border-gray-800 rounded overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-[10px] uppercase tracking-wider">
              <th className="text-left px-3 py-1.5 font-medium w-8">#</th>
              <th className="text-left px-3 py-1.5 font-medium">Symbol</th>
              <th className="text-left px-3 py-1.5 font-medium">Side</th>
              <th className="text-right px-3 py-1.5 font-medium">Score</th>
              <th className="text-right px-3 py-1.5 font-medium">Confidence</th>
              <th className="text-left px-3 py-1.5 font-medium">Decision</th>
              <th className="text-right px-3 py-1.5 font-medium">Trend</th>
              <th className="text-right px-3 py-1.5 font-medium">Volume</th>
              <th className="text-right px-3 py-1.5 font-medium">BTC</th>
              <th className="text-right px-3 py-1.5 font-medium">Risk</th>
              <th className="text-right px-3 py-1.5 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((s) => (
              <tr key={s.id} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                <td className="px-3 py-1.5 text-gray-500 tabular-nums">{s.rank}</td>
                <td className="px-3 py-1.5 text-gray-200">{s.symbol}</td>
                <td className={`px-3 py-1.5 ${s.side === "LONG" ? "text-green-400" : "text-red-400"}`}>
                  {s.side}
                </td>
                <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{s.score.toFixed(3)}</td>
                <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{s.confidence.toFixed(1)}%</td>
                <td className={`px-3 py-1.5 ${DECISION_COLORS[s.decision] || "text-gray-300"}`}>
                  {s.decision.replace("_", " ")}
                </td>
                <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{(s.trend_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{(s.volume_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{(s.btc_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{(s.risk_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-gray-300">{s.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

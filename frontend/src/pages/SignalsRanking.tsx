import { useCallback, useEffect, useState } from "react";

import type { SignalRankingRow } from "../api/signals_ranking";
import { fetchSignalsRanking } from "../api/signals_ranking";
import { ApiError } from "../api/client";

const DECISION_COLORS: Record<string, string> = {
  STRONG_APPROVE: "text-[var(--accent-green)]",
  APPROVE: "text-[var(--accent-blue)]",
  WATCH: "text-[var(--accent-yellow)]",
  REJECT: "text-[var(--accent-red)]",
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
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading signal ranking...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)] bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Retry</button>
        </div>
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        No signal data
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        Signal Leaderboard
      </h2>
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--border-subtle)] text-[var(--text-secondary)] text-[12px] uppercase tracking-wider">
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
              <tr key={s.id} className="border-t border-[var(--border-subtle)]/50 hover:bg-[var(--bg-hover)]">
                <td className="px-3 py-1.5 text-[var(--text-secondary)] tabular-nums">{s.rank}</td>
                <td className="px-3 py-1.5 text-[var(--text-primary)]">{s.symbol}</td>
                <td className={`px-3 py-1.5 ${s.side === "LONG" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {s.side}
                </td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)] tabular-nums">{s.score.toFixed(3)}</td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)] tabular-nums">{s.confidence.toFixed(1)}%</td>
                <td className={`px-3 py-1.5 ${DECISION_COLORS[s.decision] || "text-[var(--text-primary)]"}`}>
                  {s.decision.replace("_", " ")}
                </td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)] tabular-nums">{(s.trend_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)] tabular-nums">{(s.volume_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)] tabular-nums">{(s.btc_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)] tabular-nums">{(s.risk_score * 100).toFixed(0)}%</td>
                <td className="px-3 py-1.5 text-right text-[var(--text-primary)]">{s.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

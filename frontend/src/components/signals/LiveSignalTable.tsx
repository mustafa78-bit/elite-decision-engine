import ConfidenceBadge from "./ConfidenceBadge";

interface SignalRow {
  id: number;
  symbol: string;
  side: string;
  timeframe: string;
  price: number | null;
  confidence: number;
  decision: string;
  final_score: number;
  status: string;
  created_at: string | null;
}

interface Props {
  signals: SignalRow[];
}

export default function LiveSignalTable({ signals }: Props) {
  if (signals.length === 0) {
    return (
      <div className="text-[var(--text-muted)] text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No signals yet
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-[var(--text-secondary)] border-collapse">
        <thead>
          <tr className="text-[12px] uppercase text-[var(--text-muted)] border-b border-gray-800">
            <th className="text-left px-2 py-1.5 font-medium">#</th>
            <th className="text-left px-2 py-1.5 font-medium">Symbol</th>
            <th className="text-left px-2 py-1.5 font-medium">Side</th>
            <th className="text-right px-2 py-1.5 font-medium">Price</th>
            <th className="text-left px-2 py-1.5 font-medium">Decision</th>
            <th className="text-right px-2 py-1.5 font-medium">Score</th>
            <th className="text-left px-2 py-1.5 font-medium">Status</th>
            <th className="text-right px-2 py-1.5 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s, i) => (
            <tr
              key={s.id}
              className="border-b border-gray-900 hover:bg-gray-900/60 transition-colors"
            >
              <td className="px-2 py-1.5 text-[var(--text-muted)] tabular-nums">{signals.length - i}</td>
              <td className="px-2 py-1.5 font-medium text-[var(--text-primary)]">{s.symbol}</td>
              <td className="px-2 py-1.5">
                <span className={s.side === "LONG" ? "text-green-400" : "text-red-400"}>
                  {s.side}
                </span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {s.price != null ? s.price.toFixed(2) : "\u2014"}
              </td>
              <td className="px-2 py-1.5">
                <ConfidenceBadge confidence={s.confidence} decision={s.decision} />
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                <span className={s.final_score >= 0.8 ? "text-green-400" : s.final_score >= 0.5 ? "text-yellow-400" : "text-red-400"}>
                  {(s.final_score * 100).toFixed(0)}%
                </span>
              </td>
              <td className="px-2 py-1.5">
                <span className="text-[var(--text-muted)]">{s.status}</span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums text-[var(--text-muted)]">
                {s.created_at ? new Date(s.created_at).toLocaleTimeString() : "\u2014"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

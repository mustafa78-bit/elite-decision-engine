interface SignalEvent {
  id: number;
  symbol: string;
  side: string;
  confidence: number;
  decision: string;
  created_at: string | null;
}

interface Props {
  signals: SignalEvent[];
}

const decisionColors: Record<string, string> = {
  STRONG_APPROVE: "bg-green-500",
  APPROVE: "bg-blue-500",
  WATCH: "bg-yellow-500",
  REJECT: "bg-red-500",
};

export default function SignalTimeline({ signals }: Props) {
  if (signals.length === 0) {
    return (
      <div className="text-gray-600 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No signal history
      </div>
    );
  }

  const recent = signals.slice(0, 20);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        Signal Timeline
      </h3>
      <div className="space-y-1">
        {recent.map((s) => {
          const dotColor = decisionColors[s.decision] ?? "bg-gray-500";
          return (
            <div key={s.id} className="flex items-center gap-2 text-xs">
              <span className={`inline-block w-2 h-2 rounded-full ${dotColor} shrink-0`} />
              <span className="text-gray-300 font-medium w-14">{s.symbol}</span>
              <span className={s.side === "LONG" ? "text-green-400 w-8" : "text-red-400 w-8"}>
                {s.side}
              </span>
              <span className={`tabular-nums w-12 text-right ${
                s.decision === "STRONG_APPROVE" || s.decision === "APPROVE"
                  ? "text-green-400"
                  : s.decision === "WATCH"
                    ? "text-yellow-400"
                    : "text-red-400"
              }`}>
                {(s.confidence).toFixed(0)}%
              </span>
              <span className="text-gray-500 flex-1 text-right">
                {s.created_at ? new Date(s.created_at).toLocaleTimeString() : ""}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

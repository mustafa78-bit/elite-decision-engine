interface Props {
  symbol: string;
  side: string;
  confidence: number;
  decision: string;
  finalScore: number;
  trendScore: number;
  volumeScore: number;
  btcScore: number;
  riskScore: number;
}

function Bar({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-[10px] mb-0.5">
        <span className="text-[var(--text-muted)] uppercase">{label}</span>
        <span className={`tabular-nums ${color}`}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1.5 bg-gray-950 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

export default function SignalScoreCard({ symbol, side, confidence, decision, finalScore, trendScore, volumeScore, btcScore, riskScore }: Props) {
  const decisionColor = decision === "STRONG_APPROVE" || decision === "APPROVE"
    ? "text-green-400"
    : decision === "WATCH"
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">{symbol}</h3>
          <span className={side === "LONG" ? "text-green-400 text-xs" : "text-red-400 text-xs"}>{side}</span>
        </div>
        <div className="text-right">
          <div className={`text-sm font-bold ${decisionColor}`}>{decision.replace("_", " ")}</div>
          <div className="text-[10px] text-[var(--text-muted)]">{confidence.toFixed(0)}% confidence</div>
        </div>
      </div>

      <div className="border-t border-gray-800 pt-3">
        <Bar value={finalScore} label="Final" color="bg-blue-600" />
        <Bar value={trendScore} label="Trend" color="bg-green-600" />
        <Bar value={volumeScore} label="Volume" color="bg-purple-600" />
        <Bar value={btcScore} label="BTC" color="bg-orange-600" />
        <Bar value={riskScore} label="Risk" color={riskScore >= 0.5 ? "bg-red-600" : "bg-green-600"} />
      </div>
    </div>
  );
}

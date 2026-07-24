interface Props {
  scores: {
    final_score: number;
    trend_score?: number;
    volume_score?: number;
    btc_score?: number;
    risk_score?: number;
  };
}

function pct(v?: number) {
  return v != null ? `${(v * 100).toFixed(0)}%` : "\u2014";
}

export default function ScoreBreakdown({ scores }: Props) {
  const items = [
    { label: "Final", value: pct(scores.final_score) },
    { label: "Trend", value: pct(scores.trend_score) },
    { label: "Volume", value: pct(scores.volume_score) },
    { label: "BTC", value: pct(scores.btc_score) },
    { label: "Risk", value: pct(scores.risk_score) },
  ];

  return (
    <div className="flex gap-2">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-gray-950 border border-gray-800 rounded px-1.5 py-0.5 text-center min-w-[40px]"
        >
          <div className="text-[12px] text-[var(--text-muted)] uppercase">{item.label}</div>
          <div className="text-[13px] font-semibold tabular-nums text-[var(--text-primary)]">{item.value}</div>
        </div>
      ))}
    </div>
  );
}

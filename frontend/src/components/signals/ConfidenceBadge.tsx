interface Props {
  confidence: number;
  decision: string;
}

export default function ConfidenceBadge({ confidence, decision }: Props) {
  const color =
    decision === "STRONG_APPROVE"
      ? "bg-green-900 text-green-300 border-green-700"
      : decision === "APPROVE"
        ? "bg-blue-900 text-blue-300 border-blue-700"
        : decision === "WATCH"
          ? "bg-yellow-900 text-yellow-300 border-yellow-700"
          : "bg-gray-800 text-gray-400 border-gray-700";

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[10px] font-medium ${color}`}>
      <span>{decision.replace("_", " ")}</span>
      <span className="opacity-70">{(confidence).toFixed(0)}%</span>
    </div>
  );
}

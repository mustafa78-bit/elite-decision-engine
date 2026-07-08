interface Props {
  label: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
  sub?: string;
}

export default function MetricCard({ label, value, positive, negative, sub }: Props) {
  const color = positive ? "text-green-400" : negative ? "text-red-400" : "text-gray-100";
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-sm font-semibold tabular-nums ${color}`}>{value}</div>
      {sub && <div className="text-[10px] text-gray-600 mt-0.5">{sub}</div>}
    </div>
  );
}

interface Props {
  regime: string;
}

const colors: Record<string, string> = {
  TREND: "bg-green-900 text-green-300 border-green-700",
  DOWNTREND: "bg-red-900 text-red-300 border-red-700",
  RANGE: "bg-yellow-900 text-yellow-300 border-yellow-700",
  DEAD: "bg-gray-800 text-[var(--text-secondary)] border-gray-700",
};

export default function RegimeBadge({ regime }: Props) {
  const cls = colors[regime] ?? "bg-gray-800 text-[var(--text-secondary)] border-gray-700";
  return (
    <span className={`inline-block px-2 py-0.5 rounded border text-[10px] font-medium ${cls}`}>
      {regime}
    </span>
  );
}

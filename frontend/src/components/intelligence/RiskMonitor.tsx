interface Props {
  openTrades: number;
  maxOpenTrades: number;
}

export default function RiskMonitor({ openTrades, maxOpenTrades }: Props) {
  const pct = maxOpenTrades > 0 ? (openTrades / maxOpenTrades) * 100 : 0;
  const isMaxed = openTrades >= maxOpenTrades;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Risk Monitor</h3>
      <div className="text-xs">
        <div className="flex justify-between mb-1">
          <span className="text-gray-500">Open Positions</span>
          <span className={`tabular-nums font-semibold ${isMaxed ? "text-red-400" : "text-gray-200"}`}>
            {openTrades} / {maxOpenTrades}
          </span>
        </div>
        <div className="h-2 bg-gray-950 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${isMaxed ? "bg-red-600" : "bg-blue-600"}`}
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
        <div className="text-[9px] text-gray-600 mt-1">{pct.toFixed(0)}% capacity used</div>
      </div>
    </div>
  );
}

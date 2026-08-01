interface Props {
  winRate: number;
  totalTrades: number;
}

export default function WinRateChart({ winRate, totalTrades }: Props) {
  const lossRate = 100 - winRate;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        Win / Loss Rate
      </h3>
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <div className="h-4 bg-gray-950 rounded-full overflow-hidden flex">
            <div
              className="bg-green-600 h-full transition-all"
              style={{ width: `${winRate}%` }}
            />
            <div
              className="bg-red-600 h-full transition-all"
              style={{ width: `${lossRate}%` }}
            />
          </div>
        </div>
        <div className="text-xs space-y-1 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-600" />
            <span className="text-gray-300">{winRate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-600" />
            <span className="text-gray-300">{lossRate.toFixed(1)}%</span>
          </div>
        </div>
      </div>
      <p className="text-[10px] text-gray-600 mt-2">Based on {totalTrades} closed trades</p>
    </div>
  );
}

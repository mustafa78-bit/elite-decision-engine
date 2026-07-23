interface Props {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnl: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;
  maxDrawdown: number;
}

export default function PerformanceSummary({
  totalTrades,
  winningTrades,
  losingTrades,
  winRate,
  totalPnl,
  averageWin,
  averageLoss,
  profitFactor,
  maxDrawdown,
}: Props) {
  const items = [
    { label: "Total Trades", value: String(totalTrades) },
    { label: "Winning", value: String(winningTrades), color: "text-green-400" },
    { label: "Losing", value: String(losingTrades), color: "text-red-400" },
    { label: "Win Rate", value: `${winRate.toFixed(1)}%` },
    { label: "Total PnL", value: `$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? "text-green-400" : "text-red-400" },
    { label: "Avg Win", value: `$${averageWin.toFixed(2)}`, color: "text-green-400" },
    { label: "Avg Loss", value: `$${averageLoss.toFixed(2)}`, color: "text-red-400" },
    { label: "Profit Factor", value: profitFactor.toFixed(2) },
    { label: "Max Drawdown", value: `${maxDrawdown.toFixed(1)}%`, color: "text-red-400" },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Performance Summary
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2">
        {items.map((item) => (
          <div key={item.label}>
            <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">{item.label}</div>
            <div className={`text-sm font-semibold tabular-nums ${item.color || "text-[var(--text-primary)]"}`}>
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

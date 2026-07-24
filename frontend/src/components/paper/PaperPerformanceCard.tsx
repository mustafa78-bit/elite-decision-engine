interface Props {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
}

export default function PaperPerformanceCard({ totalTrades, winningTrades, losingTrades, winRate }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Paper Performance
      </h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Total</div>
          <div className="text-[var(--text-primary)] font-semibold tabular-nums">{totalTrades}</div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Win Rate</div>
          <div className="text-green-400 font-semibold tabular-nums">{winRate.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Wins</div>
          <div className="text-green-400 font-semibold tabular-nums">{winningTrades}</div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Losses</div>
          <div className="text-red-400 font-semibold tabular-nums">{losingTrades}</div>
        </div>
      </div>
    </div>
  );
}

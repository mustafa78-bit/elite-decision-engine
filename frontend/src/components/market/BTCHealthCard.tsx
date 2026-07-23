interface Props {
  btcHealthScore: number;
  ema20: number;
  ema50: number;
  ema200: number;
  volatility: number;
  volatilityScore: number;
  regimeScore: number;
}

export default function BTCHealthCard({ btcHealthScore, ema20, ema50, ema200, volatility, regimeScore }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        BTC Health
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-[var(--text-muted)]">Health Score</span>
            <span className={`text-sm font-semibold tabular-nums ${btcHealthScore >= 0.5 ? "text-green-400" : "text-red-400"}`}>
              {(btcHealthScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1.5 bg-gray-950 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${btcHealthScore >= 0.5 ? "bg-green-600" : "bg-red-600"}`}
              style={{ width: `${btcHealthScore * 100}%` }}
            />
          </div>
        </div>
        <div className="text-xs">
          <span className="text-[var(--text-muted)] block">EMA 20/50</span>
          <span className={`tabular-nums ${ema20 > ema50 ? "text-green-400" : "text-red-400"}`}>
            ${ema20.toLocaleString()} / ${ema50.toLocaleString()}
          </span>
        </div>
        <div className="text-xs">
          <span className="text-[var(--text-muted)] block">EMA 200</span>
          <span className="tabular-nums text-[var(--text-primary)]">${ema200.toLocaleString()}</span>
        </div>
        <div className="text-xs">
          <span className="text-[var(--text-muted)] block">Volatility</span>
          <span className="tabular-nums text-[var(--text-primary)]">{(volatility * 100).toFixed(3)}%</span>
        </div>
        <div className="text-xs">
          <span className="text-[var(--text-muted)] block">Regime Score</span>
          <span className={`tabular-nums ${regimeScore >= 0.5 ? "text-green-400" : "text-red-400"}`}>
            {(regimeScore * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}

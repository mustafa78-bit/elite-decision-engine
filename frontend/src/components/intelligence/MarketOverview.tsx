interface Props {
  price?: number;
  regime?: string;
  btcHealth?: number;
  volatility?: number;
  rsi?: number;
}

export default function MarketOverview({ price, regime, btcHealth, volatility, rsi }: Props) {
  const regimeColor = regime === "BULL" ? "text-green-400" : regime === "BEAR" ? "text-red-400" : "text-yellow-400";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">Market Status</h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        {price != null && (
          <div>
            <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Price</div>
            <div className="text-[var(--text-primary)] font-semibold tabular-nums">${price.toLocaleString()}</div>
          </div>
        )}
        {regime && (
          <div>
            <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Regime</div>
            <div className={`font-semibold ${regimeColor}`}>{regime}</div>
          </div>
        )}
        {btcHealth != null && (
          <div>
            <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">BTC Health</div>
            <div className="text-[var(--text-primary)] font-semibold tabular-nums">{(btcHealth * 100).toFixed(0)}%</div>
          </div>
        )}
        {volatility != null && (
          <div>
            <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Volatility</div>
            <div className="text-[var(--text-primary)] font-semibold tabular-nums">{(volatility * 100).toFixed(2)}%</div>
          </div>
        )}
        {rsi != null && (
          <div>
            <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">RSI</div>
            <div className="text-[var(--text-primary)] font-semibold tabular-nums">{rsi}</div>
          </div>
        )}
      </div>
    </div>
  );
}

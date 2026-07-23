import RegimeBadge from "./RegimeBadge";

interface Props {
  symbol: string;
  price: number;
  regime: string;
  rsi: number;
  atr: number;
}

export default function MarketCard({ symbol, price, regime, rsi, atr }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{symbol}</h3>
        <RegimeBadge regime={regime} />
      </div>
      <div className="text-2xl font-bold tabular-nums text-[var(--text-primary)] mb-3">
        ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-[var(--text-muted)]">RSI</span>
          <span className="float-right tabular-nums text-[var(--text-primary)]">{rsi.toFixed(0)}</span>
        </div>
        <div>
          <span className="text-[var(--text-muted)]">ATR</span>
          <span className="float-right tabular-nums text-[var(--text-primary)]">${atr.toFixed(0)}</span>
        </div>
      </div>
    </div>
  );
}

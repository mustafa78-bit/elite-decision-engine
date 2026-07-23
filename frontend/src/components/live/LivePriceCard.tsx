interface Props {
  symbol: string;
  price: number;
  change24h?: number;
}

export default function LivePriceCard({ symbol, price, change24h }: Props) {
  const isUp = change24h != null && change24h >= 0;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">
        {symbol} / USD
      </h3>
      <div className="text-2xl font-bold tabular-nums text-[var(--text-primary)]">
        ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      {change24h != null && (
        <div className={`text-xs mt-1 tabular-nums ${isUp ? "text-green-400" : "text-red-400"}`}>
          {isUp ? "+" : ""}{change24h.toFixed(2)}% (24h)
        </div>
      )}
    </div>
  );
}

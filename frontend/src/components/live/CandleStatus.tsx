interface Props {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function CandleStatus({ open, high, low, close, volume }: Props) {
  const isGreen = close >= open;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-2">
        Latest Candle
      </h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div>
          <span className="text-[var(--text-muted)]">Open</span>
          <span className="float-right tabular-nums text-[var(--text-secondary)]">${open.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-[var(--text-muted)]">Close</span>
          <span className={`float-right tabular-nums ${isGreen ? "text-green-400" : "text-red-400"}`}>
            ${close.toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-[var(--text-muted)]">High</span>
          <span className="float-right tabular-nums text-[var(--text-secondary)]">${high.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-[var(--text-muted)]">Low</span>
          <span className="float-right tabular-nums text-[var(--text-secondary)]">${low.toFixed(2)}</span>
        </div>
        <div className="col-span-2">
          <span className="text-[var(--text-muted)]">Volume</span>
          <span className="float-right tabular-nums text-[var(--text-secondary)]">
            {volume >= 1_000_000
              ? `${(volume / 1_000_000).toFixed(2)}M`
              : volume.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

interface Props {
  entry: number;
  atr: number;
  onEntryChange: (v: number) => void;
  onAtrChange: (v: number) => void;
  quantity: string;
  notional: string;
  riskAmount: string;
}

export default function PositionSizeCard({
  entry, atr, onEntryChange, onAtrChange,
  quantity, notional, riskAmount,
}: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Position Size Calculator
      </h3>
      <div className="space-y-2 mb-3">
        <div>
          <label className="text-[10px] text-[var(--text-muted)] block mb-0.5">Entry Price</label>
          <input
            type="number"
            value={entry}
            onChange={(e) => onEntryChange(Number(e.target.value))}
            className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1 text-xs text-[var(--text-primary)] tabular-nums"
          />
        </div>
        <div>
          <label className="text-[10px] text-[var(--text-muted)] block mb-0.5">ATR</label>
          <input
            type="number"
            value={atr}
            onChange={(e) => onAtrChange(Number(e.target.value))}
            className="w-full bg-gray-950 border border-gray-700 rounded px-2 py-1 text-xs text-[var(--text-primary)] tabular-nums"
          />
        </div>
      </div>
      <div className="border-t border-gray-800 pt-2 space-y-1">
        <Row label="Quantity" value={quantity} />
        <Row label="Notional" value={`$${notional}`} />
        <Row label="Risk Amount" value={`$${riskAmount}`} negative />
      </div>
    </div>
  );
}

function Row({ label, value, negative }: { label: string; value: string; negative?: boolean }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-[var(--text-muted)]">{label}</span>
      <span className={`tabular-nums ${negative ? "text-red-400" : "text-[var(--text-primary)]"}`}>{value}</span>
    </div>
  );
}

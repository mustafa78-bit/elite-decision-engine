interface Props {
  equity: number;
  totalPnl: number;
  unrealizedPnl: number;
}

export default function BalanceCard({ equity, totalPnl, unrealizedPnl }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Balance
      </h3>
      <div className="text-2xl font-bold tabular-nums text-[var(--text-primary)]">
        ${equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-[var(--text-muted)]">Realized PnL</span>
          <span className={`float-right tabular-nums ${totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            ${totalPnl.toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-[var(--text-muted)]">Unrealized</span>
          <span className={`float-right tabular-nums ${unrealizedPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            ${unrealizedPnl.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

interface Props {
  open: number;
  closed: number;
  totalPnl: number;
}

export default function TradeMonitor({ open, closed, totalPnl }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-3">Trade Monitor</h3>
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <div className="text-[var(--text-muted)] text-[9px] uppercase tracking-wider">Open</div>
          <div className="text-blue-400 font-semibold tabular-nums">{open}</div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[9px] uppercase tracking-wider">Closed</div>
          <div className="text-[var(--text-primary)] font-semibold tabular-nums">{closed}</div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[9px] uppercase tracking-wider">Total PnL</div>
          <div className={`font-semibold tabular-nums ${totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            ${totalPnl.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}

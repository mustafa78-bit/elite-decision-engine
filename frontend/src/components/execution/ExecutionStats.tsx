interface Props {
  signals: {
    total: number;
    approved: number;
    rejected: number;
    pending: number;
    execution_rate: number;
  };
  trades: {
    total: number;
    open: number;
    closed: number;
    tp_hit: number;
    sl_hit: number;
  };
}

export default function ExecutionStats({ signals, trades }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Execution Statistics
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Signals Total</div>
          <div className="text-lg font-semibold tabular-nums text-[var(--text-primary)]">{signals.total}</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Execution Rate</div>
          <div className="text-lg font-semibold tabular-nums text-green-400">{signals.execution_rate}%</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Approved</div>
          <div className="text-lg font-semibold tabular-nums text-green-400">{signals.approved}</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Rejected</div>
          <div className="text-lg font-semibold tabular-nums text-red-400">{signals.rejected}</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Trades Total</div>
          <div className="text-lg font-semibold tabular-nums text-[var(--text-primary)]">{trades.total}</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Open</div>
          <div className="text-lg font-semibold tabular-nums text-blue-400">{trades.open}</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">TP Hit</div>
          <div className="text-lg font-semibold tabular-nums text-green-400">{trades.tp_hit}</div>
        </div>
        <div>
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">SL Hit</div>
          <div className="text-lg font-semibold tabular-nums text-red-400">{trades.sl_hit}</div>
        </div>
      </div>
    </div>
  );
}

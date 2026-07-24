interface Props {
  allocation: Record<string, number>;
}

export default function ExposureChart({ allocation }: Props) {
  const entries = Object.entries(allocation);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  if (entries.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
          Exposure
        </h3>
        <p className="text-[var(--text-muted)] text-xs text-center py-4">No open positions</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Exposure by Symbol
      </h3>
      <div className="space-y-2">
        {entries.map(([symbol, exposure]) => {
          const pct = total > 0 ? (exposure / total) * 100 : 0;
          return (
            <div key={symbol}>
              <div className="flex justify-between text-[13px] mb-0.5">
                <span className="text-[var(--text-secondary)]">{symbol}</span>
                <span className="text-[var(--text-secondary)] tabular-nums">
                  ${exposure.toFixed(0)} ({pct.toFixed(0)}%)
                </span>
              </div>
              <div className="h-2 bg-gray-950 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

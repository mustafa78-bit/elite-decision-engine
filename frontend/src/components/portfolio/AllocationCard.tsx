interface Props {
  allocation: Record<string, number>;
}

export default function AllocationCard({ allocation }: Props) {
  const entries = Object.entries(allocation);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  if (entries.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
          Allocation
        </h3>
        <p className="text-gray-600 text-xs text-center py-4">No data</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        Allocation
      </h3>
      <div className="space-y-1">
        {entries.map(([symbol, value]) => (
          <div key={symbol} className="flex items-center justify-between text-xs">
            <span className="text-gray-300">{symbol}</span>
            <div className="flex items-center gap-3">
              <div className="w-24 bg-gray-950 rounded-full h-1.5 overflow-hidden">
                <div
                  className="h-full bg-purple-600 rounded-full"
                  style={{ width: `${total > 0 ? (value / total) * 100 : 0}%` }}
                />
              </div>
              <span className="text-gray-400 tabular-nums w-20 text-right">
                ${value.toFixed(0)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

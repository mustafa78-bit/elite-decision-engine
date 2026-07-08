interface Props {
  totalPnl: number;
  openTrades: number;
  closedTrades: number;
}

export default function PaperPnLCard({ totalPnl, openTrades, closedTrades }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">
        Paper PnL
      </h3>
      <div className={`text-2xl font-bold tabular-nums ${totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
        ${totalPnl.toFixed(2)}
      </div>
      <div className="mt-2 text-xs text-gray-500">
        {openTrades} open / {closedTrades} closed
      </div>
    </div>
  );
}

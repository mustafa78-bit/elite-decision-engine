interface Props {
  total: number;
  open: number;
  approved: number;
  rejected: number;
}

export default function SignalFeed({ total, open, approved, rejected }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">Signal Feed</h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">Total</div>
          <div className="text-gray-200 font-semibold tabular-nums">{total}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">Open</div>
          <div className="text-yellow-400 font-semibold tabular-nums">{open}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">Approved</div>
          <div className="text-green-400 font-semibold tabular-nums">{approved}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">Rejected</div>
          <div className="text-red-400 font-semibold tabular-nums">{rejected}</div>
        </div>
      </div>
    </div>
  );
}

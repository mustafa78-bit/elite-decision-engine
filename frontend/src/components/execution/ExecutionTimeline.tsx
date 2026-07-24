interface Props {
  approved: number;
  rejected: number;
  pending: number;
}

export default function ExecutionTimeline({ approved, rejected, pending }: Props) {
  const total = approved + rejected + pending;
  const approvedPct = total > 0 ? (approved / total) * 100 : 0;
  const rejectedPct = total > 0 ? (rejected / total) * 100 : 0;
  const pendingPct = total > 0 ? (pending / total) * 100 : 0;

  if (total === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">Signal Flow</h3>
        <p className="text-[var(--text-muted)] text-xs text-center py-4">No signal data</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">Signal Flow</h3>
      <div className="h-6 bg-gray-950 rounded-full overflow-hidden flex">
        <div className="bg-green-600 h-full transition-all" style={{ width: `${approvedPct}%` }} title={`Approved: ${approved}`} />
        <div className="bg-red-600 h-full transition-all" style={{ width: `${rejectedPct}%` }} title={`Rejected: ${rejected}`} />
        <div className="bg-yellow-600 h-full transition-all" style={{ width: `${pendingPct}%` }} title={`Pending: ${pending}`} />
      </div>
      <div className="flex gap-4 mt-2 text-[12px]">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-600" />
          <span className="text-[var(--text-secondary)]">{approved} approved</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-600" />
          <span className="text-[var(--text-secondary)]">{rejected} rejected</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-yellow-600" />
          <span className="text-[var(--text-secondary)]">{pending} pending</span>
        </div>
      </div>
    </div>
  );
}

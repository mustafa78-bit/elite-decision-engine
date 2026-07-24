interface Props {
  label: string
  status: string
  detail?: string
}

const statusColor: Record<string, string> = {
  ONLINE: "#22C55E",
  DEGRADED: "#FACC15",
  OFFLINE: "#EF4444",
}

export default function SubsystemRow({ label, status, detail }: Props) {
  const color = statusColor[status] ?? "#64748B"
  const ariaLabel = `${label}: ${status}${detail ? `, ${detail}` : ""}`
  return (
    <div className="flex items-center justify-between py-1 text-[12px] font-mono" role="status" aria-label={ariaLabel}>
      <span className="text-[var(--text-muted)]">{label}</span>
      <div className="flex items-center gap-1.5">
        <span className="w-1 h-1 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
        <span style={{ color }}>{status}</span>
        {detail && <span className="text-[var(--text-muted)] ml-0.5">{detail}</span>}
      </div>
    </div>
  )
}

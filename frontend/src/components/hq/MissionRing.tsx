import { useRef, useEffect, useState } from "react"
import type { SubsystemStatus } from "../../types/system"

interface SectorData {
  label: string
  status: SubsystemStatus
}

interface Props {
  sectors: SectorData[]
}

const sectorColors: Record<SubsystemStatus, string> = {
  ONLINE: "#3EDC97",
  OFFLINE: "#FF5D73",
  DEGRADED: "#FFB547",
  UNKNOWN: "#6B7891",
}

const sectorLabels: Record<SubsystemStatus, string> = {
  ONLINE: "Online",
  OFFLINE: "Offline",
  DEGRADED: "Degraded",
  UNKNOWN: "Unknown",
}

function sectorPulseClass(status: SubsystemStatus): string {
  switch (status) {
    case "ONLINE": return "sector-pulse-online"
    case "DEGRADED": return "sector-pulse-warning"
    case "OFFLINE": return "sector-pulse-critical"
    default: return ""
  }
}

function Sector({ label, status }: { label: string; status: SubsystemStatus }) {
  const color = sectorColors[status]
  const [pulse, setPulse] = useState(false)
  const prevRef = useRef(status)

  useEffect(() => {
    if (prevRef.current !== status) {
      setPulse(true)
      const timer = setTimeout(() => setPulse(false), 600)
      prevRef.current = status
      return () => clearTimeout(timer)
    }
  }, [status])

  return (
    <div className="flex items-center gap-2">
      {/* Status dot */}
      <div className="relative flex items-center justify-center" style={{ width: 10, height: 10 }}>
        <div
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            backgroundColor: color,
            opacity: status === "UNKNOWN" ? 0.3 : 0.85,
            transition: "background-color 0.3s ease, opacity 0.3s ease",
            animation: pulse ? `${sectorPulseClass(status)} 0.6s ease-out` : undefined,
          }}
        />
      </div>
      <div className="flex flex-col">
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
            transition: "color 0.3s ease",
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: color,
            opacity: 0.5,
            transition: "color 0.3s ease, opacity 0.3s ease",
          }}
        >
          {sectorLabels[status]}
        </span>
      </div>
    </div>
  )
}

export default function MissionRing({ sectors }: Props) {
  return (
    <div className="flex flex-col items-center justify-center" style={{ padding: "8px 0" }}>
      {/* OLLO Center */}
      <div
        className="relative flex items-center justify-center"
        style={{ width: 120, height: 120 }}
      >
        {/* Outer ring — static */}
        <div
          className="absolute rounded-full"
          style={{
            width: 110,
            height: 110,
            border: "1px solid rgba(120,150,210,0.06)",
          }}
        />
        {/* Inner ring — static */}
        <div
          className="absolute rounded-full"
          style={{
            width: 90,
            height: 90,
            border: "1px solid rgba(120,150,210,0.04)",
          }}
        />
      </div>

      {/* Sectors — fixed grid below OLLO */}
      <div
        className="grid grid-cols-3 gap-x-6 gap-y-1.5"
        style={{ marginTop: 12 }}
      >
        {sectors.map((s) => (
          <Sector key={s.label} label={s.label} status={s.status} />
        ))}
      </div>
    </div>
  )
}

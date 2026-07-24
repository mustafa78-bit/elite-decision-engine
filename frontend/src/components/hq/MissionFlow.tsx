import { useRef, useEffect, useState } from "react"

interface FlowNode {
  label: string
  active: boolean
  color: string
}

interface Props {
  nodes: FlowNode[]
}

const nodeIcons: Record<string, string> = {
  Scanner: "⟡",
  Whale: "◈",
  Council: "◉",
  Evidence: "◎",
  Decision: "◆",
  Founder: "▲",
  Action: "▶",
}

function Node({ node }: { node: FlowNode }) {
  const [pulse, setPulse] = useState(false)
  const prevRef = useRef(node.active)
  const icon = nodeIcons[node.label] || "●"

  useEffect(() => {
    if (prevRef.current !== node.active) {
      setPulse(true)
      const timer = setTimeout(() => setPulse(false), 600)
      prevRef.current = node.active
      return () => clearTimeout(timer)
    }
  }, [node.active])

  return (
    <div className="flex flex-col items-center gap-1" style={{ minWidth: 44 }}>
      <div
        className="flex items-center justify-center"
        style={{
          width: 22,
          height: 22,
          borderRadius: "50%",
          backgroundColor: node.active ? `${node.color}12` : "transparent",
          border: `0.5px solid ${node.active ? node.color : "var(--border-subtle)"}`,
          color: node.active ? node.color : "var(--text-muted)",
          opacity: node.active ? 1 : 0.3,
          transition: "all 0.3s ease",
          animation: pulse ? "node-pulse 0.6s ease-out" : undefined,
        }}
      >
        <span style={{ fontSize: 11 }}>{icon}</span>
      </div>
      <span
        style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: node.active ? node.color : "var(--text-muted)",
          opacity: node.active ? 1 : 0.3,
          transition: "all 0.3s ease",
        }}
      >
        {node.label}
      </span>
    </div>
  )
}

export default function MissionFlow({ nodes }: Props) {
  if (nodes.length === 0) return null

  const activeCount = nodes.filter((n) => n.active).length

  return (
    <div>
      <div className="hq-section-label">Mission Flow</div>
      <div className="flex items-center justify-center gap-0">
        {nodes.map((node, i) => (
          <div key={node.label} className="flex items-center">
            <Node node={node} />
            {i < nodes.length - 1 && (
              <div
                className="shrink-0"
                style={{
                  width: 16,
                  height: 1,
                  backgroundColor: node.active ? "var(--border-subtle)" : "var(--border-subtle)",
                  opacity: node.active ? 0.4 : 0.15,
                  margin: "0 2px",
                }}
              />
            )}
          </div>
        ))}
      </div>
      <div
        className="text-center mt-2 text-[11px] font-mono"
        style={{ color: "var(--text-muted)" }}
      >
        {activeCount}/{nodes.length} online
      </div>
    </div>
  )
}

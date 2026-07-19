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
    <div className="flex flex-col items-center gap-1 min-w-[34px] sm:min-w-[44px]">
      <div
        className="flex items-center justify-center rounded-full transition-all duration-300"
        style={{
          width: "18px",
          height: "18px",
          backgroundColor: node.active ? `${node.color}12` : "transparent",
          border: `0.5px solid ${node.active ? node.color : "var(--border-subtle)"}`,
          color: node.active ? node.color : "var(--text-muted)",
          opacity: node.active ? 1 : 0.3,
          animation: pulse ? "node-pulse 0.6s ease-out" : undefined,
        }}
      >
        <span className="text-[6px] sm:text-[7px]">{icon}</span>
      </div>
      <span
        className="text-[6px] sm:text-[7px] font-semibold uppercase tracking-wider transition-all duration-300"
        style={{
          color: node.active ? node.color : "var(--text-muted)",
          opacity: node.active ? 1 : 0.3,
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
      <div className="flex items-center justify-center gap-0 overflow-x-hidden px-1">
        {nodes.map((node, i) => (
          <div key={node.label} className="flex items-center">
            <Node node={node} />
            {i < nodes.length - 1 && (
              <div
                className="shrink-0 h-[1px] mx-0.5 transition-all duration-300 w-[6px] sm:w-[16px]"
                style={{
                  backgroundColor: "var(--border-subtle)",
                  opacity: node.active ? 0.4 : 0.15,
                }}
              />
            )}
          </div>
        ))}
      </div>
      <div
        className="text-center mt-2 text-[7px] font-mono"
        style={{ color: "var(--text-muted)" }}
      >
        {activeCount}/{nodes.length} online
      </div>
    </div>
  )
}

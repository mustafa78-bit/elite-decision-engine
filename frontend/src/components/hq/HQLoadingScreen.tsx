import { useEffect, useState } from "react"
import { motion } from "framer-motion"

interface SyncStep {
  label: string
  status: "pending" | "syncing" | "done"
}

const INITIAL_STEPS: SyncStep[] = [
  { label: "AI Foundation", status: "pending" },
  { label: "Evidence Engine", status: "pending" },
  { label: "Risk Engine", status: "pending" },
  { label: "Council", status: "pending" },
  { label: "Mission", status: "pending" },
]

const TOTAL_DURATION = 1000

export default function HQLoadingScreen() {
  const [steps, setSteps] = useState<SyncStep[]>(INITIAL_STEPS)
  const [visible, setVisible] = useState(true)
  const [done, setDone] = useState(false)

  useEffect(() => {
    const startTime = Date.now()
    const stepDuration = TOTAL_DURATION / INITIAL_STEPS.length

    const timers: ReturnType<typeof setTimeout>[] = []

    INITIAL_STEPS.forEach((_, i) => {
      const timer = setTimeout(() => {
        setSteps((prev) =>
          prev.map((s, j) => {
            if (j === i) return { ...s, status: "syncing" as const }
            if (j < i) return { ...s, status: "done" as const }
            return s
          }),
        )

        // Mark as done after brief syncing delay
        setTimeout(() => {
          setSteps((prev) =>
            prev.map((s, j) => {
              if (j === i) return { ...s, status: "done" as const, label: i === INITIAL_STEPS.length - 1 ? "READY" : s.label }
              return s
            }),
          )
          if (i === INITIAL_STEPS.length - 1) {
            setTimeout(() => {
              setDone(true)
              setTimeout(() => setVisible(false), 400)
            }, 200)
          }
        }, stepDuration * 0.3)
      }, startTime + i * stepDuration - Date.now())

      timers.push(timer)
    })

    return () => timers.forEach(clearTimeout)
  }, [])

  if (!visible) return null

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center"
      style={{
        backgroundColor: "var(--bg-deep)",
      }}
      animate={{
        opacity: done ? 0 : 1,
      }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      {/* Title */}
      <div className="text-center mb-12">
        <div
          className="text-[11px] font-semibold uppercase tracking-[0.25em]"
          style={{ color: "var(--text-muted)" }}
        >
          ELITE
        </div>
        <div
          className="text-[13px] font-semibold uppercase tracking-[0.3em] mt-2"
          style={{ color: "var(--text-primary)" }}
        >
          COMMAND HEADQUARTERS
        </div>
      </div>

      {/* Sync steps */}
      <div className="space-y-2" style={{ minWidth: 240 }}>
        {steps.map((step) => (
          <div
            key={step.label}
            className="flex items-center justify-between"
            style={{
              opacity: step.status === "pending" ? 0.25 : 1,
              transition: "opacity 0.3s ease",
            }}
          >
            <div className="flex items-center gap-3">
              <span
                className="rounded-full"
                style={{
                  width: 4,
                  height: 4,
                  backgroundColor:
                    step.status === "done" ? "#3EDC97" :
                    step.status === "syncing" ? "#4F8CFF" :
                    "var(--text-muted)",
                  opacity: step.status === "pending" ? 0.3 : 0.8,
                  transition: "all 0.3s ease",
                }}
              />
              <span
                className="font-mono"
                style={{
                  fontSize: 9,
                  color:
                    step.status === "done" ? "var(--text-secondary)" :
                    step.status === "syncing" ? "var(--accent-blue)" :
                    "var(--text-muted)",
                  letterSpacing: "0.08em",
                  transition: "color 0.3s ease",
                }}
              >
                {step.label}
              </span>
            </div>
            <span
              className="font-mono"
              style={{
                fontSize: 7,
                color:
                  step.status === "done" ? "#3EDC97" :
                  step.status === "syncing" ? "#4F8CFF" :
                  "var(--text-muted)",
                opacity: step.status === "pending" ? 0.3 : 0.7,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                transition: "all 0.3s ease",
              }}
            >
              {step.status === "done" ? (step.label === "READY" ? "READY" : "ONLINE") :
               step.status === "syncing" ? "..." :
               "....."}
            </span>
          </div>
        ))}
      </div>

      {/* Loading indicator */}
      <div className="flex items-center gap-1 mt-10">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="rounded-full"
            style={{
              width: 3,
              height: 3,
              backgroundColor: "var(--text-muted)",
              opacity: done ? 0 : 0.2,
              animation: done ? "none" : `loading-dot 1.4s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
    </motion.div>
  )
}

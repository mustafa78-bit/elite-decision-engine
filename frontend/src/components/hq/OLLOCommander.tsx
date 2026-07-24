import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import type { OLLOResponse, OLLOBriefing } from "../../types/ollo"

interface Props {
  greeting: OLLOResponse | null
  briefing: OLLOBriefing | null
  loading: boolean
  error: string | null
}

type DisplayMode = "greeting" | "briefing"

export default function OLLOCommander({ greeting, briefing, loading, error }: Props) {
  const [mode, setMode] = useState<DisplayMode>("greeting")

  useEffect(() => {
    if (briefing && !greeting) setMode("briefing")
  }, [briefing, greeting])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div
          className="rounded-full"
          style={{
            width: 80,
            height: 80,
            background: "radial-gradient(circle at 35% 35%, rgba(79,140,255,0.1), rgba(79,140,255,0.02), transparent)",
            border: "1px solid rgba(79,140,255,0.06)",
            animation: "ollo-breathe 3s ease-in-out infinite",
          }}
        />
        <div className="h-1.5 skeleton-pulse w-24 mt-5" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div
          className="rounded-full flex items-center justify-center"
          style={{
            width: 64,
            height: 64,
            border: "1px solid rgba(255, 93, 115, 0.15)",
            background: "rgba(255, 93, 115, 0.03)",
          }}
        >
          <span className="text-lg" style={{ color: "rgba(255, 93, 115, 0.4)" }}>◉</span>
        </div>
        <p className="mt-3 text-[12px] font-mono" style={{ color: "rgba(255, 93, 115, 0.6)" }}>{error}</p>
      </div>
    )
  }

  const displayBriefing = mode === "briefing" && briefing

  return (
    <div className="flex flex-col items-center justify-center py-10">
      {/* OLLO Orb — calm, breathing, volumetric */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
      >
        <div
          className="rounded-full"
          style={{
            width: 80,
            height: 80,
            background: "radial-gradient(circle at 35% 30%, rgba(79,140,255,0.15) 0%, rgba(79,140,255,0.03) 40%, transparent 65%)",
            border: "1px solid rgba(79,140,255,0.1)",
            animation: "ollo-breathe 5s ease-in-out infinite, ollo-glow 5s ease-in-out infinite",
          }}
        />
      </motion.div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {displayBriefing ? (
          <motion.div
            key="briefing"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="text-center mt-4"
            style={{ maxWidth: 340 }}
          >
            <div
              className="text-[11px] font-medium uppercase tracking-[0.18em] mb-2"
              style={{ color: "var(--accent-blue)" }}
            >
              {briefing!.kind} Briefing
            </div>
            <h3 className="text-sm font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
              {briefing!.title}
            </h3>
            <p className="text-[13px] mt-2 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {briefing!.text}
            </p>
            <div className="mt-3 text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>
              {briefing!.provider} · {briefing!.model}
            </div>
          </motion.div>
        ) : greeting ? (
          <motion.div
            key="greeting"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="text-center mt-4"
            style={{ maxWidth: 340 }}
          >
            <h3 className="text-sm font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
              {greeting!.text.split("\n")[0] || "Welcome, Commander."}
            </h3>
            {greeting!.sections && greeting!.sections.length > 0 ? (
              <div className="space-y-2 text-left mt-3">
                {greeting!.sections.map((section, i) => (
                  <div key={i}>
                    <div className="text-[11px] font-medium uppercase tracking-[0.12em] mb-0.5" style={{ color: "var(--accent-blue)" }}>
                      {section.heading}
                    </div>
                    <p className="text-[13px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                      {section.content}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[13px] mt-2 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {greeting!.text}
              </p>
            )}
            <div className="mt-3 text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>
              {greeting!.provider} · {greeting!.model} · {(greeting!.duration_ms / 1000).toFixed(1)}s
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center mt-4"
          >
            <p className="text-[13px]" style={{ color: "var(--text-muted)" }}>
              Awaiting OLLO connection...
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

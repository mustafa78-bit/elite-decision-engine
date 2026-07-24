import { useEffect, useState } from "react";
import type { TradeIntelligence } from "../../types/trade";
import type { AgentReportData, CouncilReportData } from "../../api/council";
import { evaluateSymbol } from "../../api/council";

const DIRECTION_COLORS: Record<string, string> = {
  BULLISH: "#22C55E",
  BEARISH: "#EF4444",
  NEUTRAL: "#FACC15",
  PASS: "#64748B",
};

const MEMBER_COLORS: Record<string, string> = {
  Technical: "#60a5fa",
  Trend: "#a78bfa",
  Risk: "#f59e0b",
  News: "#34d399",
  Whale: "#f472b6",
  Macro: "#38bdf8",
};

interface Props {
  intelligence?: TradeIntelligence | null;
  symbol?: string;
}

export default function AICouncilWidget({ intelligence, symbol = "BTCUSDT" }: Props) {
  const [report, setReport] = useState<CouncilReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const intelligenceOnly = !!(intelligence && !report);
  const activeData: CouncilReportData | null = !intelligenceOnly ? report : null;

  useEffect(() => {
    if (intelligence) {
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    evaluateSymbol(symbol)
      .then((res) => {
        setReport(res.council_report);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to fetch council data");
      })
      .finally(() => setLoading(false));
  }, [symbol, intelligence]);

  if (loading) {
    return (
      <div className="w-full rounded-xl overflow-hidden glass-card">
        <div className="px-4 py-2.5 border-b" style={{ borderColor: "#243244" }}>
          <span className="glass-header-label">AI COUNCIL</span>
        </div>
        <div className="p-4 space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="h-2.5 w-16 rounded skeleton-pulse" style={{ background: "#243244" }} />
                <div className="h-2.5 w-20 rounded skeleton-pulse" style={{ background: "#243244" }} />
              </div>
              <div className="h-1.5 w-full rounded-full" style={{ background: "#1E293B" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || (!activeData && !intelligenceOnly)) {
    return (
      <div className="w-full rounded-xl overflow-hidden glass-card">
        <div className="px-4 py-2.5 border-b" style={{ borderColor: "#243244" }}>
          <span className="glass-header-label">AI COUNCIL</span>
        </div>
        <div className="p-6 text-center">
          <span className="text-[12px] font-mono" style={{ color: "var(--text-muted)" }}>
            {error || "No council data yet"}
          </span>
        </div>
      </div>
    );
  }

  if (intelligenceOnly && intelligence) {
    const dirColor = intelligence.decision === "BUY" ? "#22C55E" : intelligence.decision === "SELL" ? "#EF4444" : "#FACC15";
    return (
      <div className="w-full rounded-xl overflow-hidden glass-card">
        <div className="px-4 py-2.5 border-b flex items-center justify-between" style={{ borderColor: "#243244" }}>
          <span className="glass-header-label">AI COUNCIL</span>
          <span className="text-[11px] font-mono" style={{ color: "rgba(139,92,246,0.5)" }}>
            LIVE
          </span>
        </div>
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-mono" style={{ color: "var(--text-secondary)" }}>Decision</span>
            <span className="text-[13px] font-mono font-semibold" style={{ color: dirColor }}>{intelligence.decision}</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-mono" style={{ color: "var(--text-secondary)" }}>Confidence</span>
              <span className="text-[12px] font-mono" style={{ color: dirColor }}>{(intelligence.confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "#0D1320" }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(intelligence.confidence * 100, 100)}%`,
                  background: `linear-gradient(to right, ${dirColor}, ${dirColor}cc)`,
                  animation: "progressFill 0.6s ease-out both",
                }}
              />
            </div>
          </div>
          <div className="space-y-1.5 pt-1 border-t" style={{ borderColor: "#243244" }}>
            {[
              { label: "Trend", value: intelligence.trend_score, color: "#60a5fa" },
              { label: "Volume", value: intelligence.volume_score, color: "#34d399" },
              { label: "BTC Health", value: intelligence.btc_score, color: "#38bdf8" },
              { label: "Risk", value: intelligence.risk_score, color: "#f59e0b" },
            ].map((m) => (
              <div key={m.label} className="space-y-0.5">
                <div className="flex items-center justify-between text-[12px] font-mono">
                  <span style={{ color: "var(--text-secondary)" }}>{m.label}</span>
                  <span style={{ color: m.color }}>{(m.value * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: "#0D1320" }}>
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(m.value * 100, 100)}%`,
                      background: m.color,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!activeData) return null;

  const consensusColor = DIRECTION_COLORS[activeData.consensus_direction] ?? "#64748B";

  return (
    <div className="w-full rounded-xl overflow-hidden glass-card">
      <div className="px-4 py-2.5 border-b flex items-center justify-between" style={{ borderColor: "#243244" }}>
        <span className="glass-header-label">AI COUNCIL</span>
        <span className="text-[11px] font-mono" style={{ color: "rgba(139,92,246,0.5)" }}>
          {activeData.agent_count} AGENTS
        </span>
      </div>

      <div className="p-4 space-y-3">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[12px] font-mono" style={{ color: "var(--text-secondary)" }}>Consensus</span>
            <span className="text-[12px] font-mono font-semibold" style={{ color: consensusColor }}>
              {activeData.consensus_direction}
            </span>
          </div>
          <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "#0D1320" }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min(activeData.consensus_score * 100, 100)}%`,
                background: `linear-gradient(to right, ${consensusColor}, ${consensusColor}cc)`,
                boxShadow: `0 0 6px ${consensusColor}44`,
                animation: "progressFill 0.6s ease-out both",
              }}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono" style={{ color: "var(--text-disabled)" }}>
              Confidence: {(activeData.consensus_score * 100).toFixed(0)}%
            </span>
            <span className="text-[11px] font-mono" style={{ color: "var(--text-disabled)" }}>
              Agreement: {activeData.agreement_level}
            </span>
          </div>
        </div>

        <div className="space-y-1.5 pt-1 border-t" style={{ borderColor: "#243244" }}>
          <span className="text-[11px] font-medium tracking-[0.08em]" style={{ color: "var(--text-muted)" }}>MEMBERS</span>
          {activeData.agent_reports.map((agent: AgentReportData) => {
            const agentColor = MEMBER_COLORS[agent.agent_name] ?? "#64748B";
            const dirColor = DIRECTION_COLORS[agent.direction] ?? "#64748B";
            return (
              <div key={agent.agent_name} className="space-y-1">
                <div className="flex items-center justify-between text-[12px] font-mono">
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ backgroundColor: agentColor }} />
                    <span style={{ color: "var(--text-secondary)" }}>{agent.agent_name}</span>
                  </div>
                  <span style={{ color: dirColor }}>
                    {agent.direction} ({(agent.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: "#0D1320" }}>
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(agent.confidence * 100, 100)}%`,
                      background: `linear-gradient(to right, ${agentColor}, ${agentColor}99)`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-center justify-between pt-1 border-t" style={{ borderColor: "#243244" }}>
          <span className="text-[11px] font-mono" style={{ color: "var(--text-disabled)" }}>
            {activeData.sources_agreeing}/{activeData.agent_count} agreeing
          </span>
          <span className="text-[11px] font-mono" style={{ color: "var(--text-disabled)" }}>
            {(activeData.consensus_score * 100).toFixed(0)}% score
          </span>
        </div>
      </div>
    </div>
  );
}
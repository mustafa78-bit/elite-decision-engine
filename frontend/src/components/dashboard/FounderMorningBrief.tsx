import { useState, useEffect } from "react"
import { Card, CardContent } from "../ui/card"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"
import { Badge } from "../ui/badge"
import { useApi } from "../../hooks/useApi"
import { fetchMorningBrief } from "../../api/ollo"

export default function FounderMorningBrief() {
  const { data, loading, error, refetch } = useApi(fetchMorningBrief, [])
  const [secondsSinceRefresh, setSecondsSinceRefresh] = useState(0)

  // Auto-refresh interval of 30 seconds to simulate a live-ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsSinceRefresh((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Force refetch and reset timer
  const handleManualRefresh = () => {
    refetch()
    setSecondsSinceRefresh(0)
  }

  if (loading && !data) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-10 w-full rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-32 w-full rounded" />
          <Skeleton className="h-32 w-full rounded" />
        </div>
        <Skeleton className="h-20 w-full rounded" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-[var(--accent-red)] bg-black/40">
        <CardContent className="p-6 text-center space-y-3">
          <p className="text-sm font-semibold text-[var(--accent-red)]">Failed to load "The 30-Second Morning" HUD</p>
          <p className="text-xs text-[var(--text-muted)]">Check API connectivity or database state.</p>
          <Button variant="outline" size="sm" onClick={handleManualRefresh}>
            Retry Load
          </Button>
        </CardContent>
      </Card>
    )
  }

  const brief = data || {
    market_regime_banner: { regime: "UNKNOWN", trend: "NEUTRAL", volatility: "NORMAL" },
    overnight_summary: "Awaiting overnight metrics compile...",
    attention_required: [{ type: "INFO", message: "Nominal constraints verified. Standard controls active.", action: "No action required." }],
    portfolio_risk: { score: 100, status: "Excellent", contributors: ["✓ Baseline risk active"], recommended_action: "No immediate action." },
    best_opportunities: [],
    whats_changed: { regime_shift: "Regime holding steady.", active_exposure_change: "Exposure delta unchanged.", new_signals_count: "Zero new scanner signals." },
    ai_council_summary: { consensus: "Awaiting advisor weight tally...", confidence: "Medium", advisor_weights: "Default" },
    important_action: { action: "Maintain active holds.", priority: "LOW", rationale: "System holds optimal portfolio health." }
  }

  const regime = brief.market_regime_banner
  const portfolio = brief.portfolio_risk
  const opportunities = brief.best_opportunities
  const attention = brief.attention_required
  const changes = brief.whats_changed
  const importantAction = brief.important_action

  // Determine colors based on status/priority
  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case "EXCELLENT":
      case "HEALTHY":
        return "var(--accent-green, #3EDC97)"
      case "CAUTION":
        return "var(--accent-yellow, #FFB547)"
      case "CRITICAL":
      case "HIGH":
        return "var(--accent-red, #FF5D73)"
      default:
        return "var(--text-muted, #6B7891)"
    }
  }

  return (
    <div className="space-y-4">
      {/* ====== LIVE REGIME BANNER ====== */}
      <div
        className="flex flex-col md:flex-row items-center justify-between p-3 rounded-lg border text-xs"
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.4)",
          borderColor: "var(--border-subtle)",
        }}
      >
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full animate-pulse bg-[var(--accent-green)]" />
          <span className="font-semibold uppercase tracking-wider text-[var(--text-primary)]">
            MARKET REGIME: {regime.regime}
          </span>
          <span className="text-[var(--text-muted)]">|</span>
          <span className="text-[var(--text-secondary)] font-mono">
            Trend: <span style={{ color: getStatusColor(regime.trend === "BULLISH" ? "HEALTHY" : regime.trend === "BEARISH" ? "CRITICAL" : "NEUTRAL") }}>{regime.trend}</span>
          </span>
          <span className="text-[var(--text-muted)]">|</span>
          <span className="text-[var(--text-secondary)] font-mono">
            Volatility: <span className="text-[var(--accent-yellow)]">{regime.volatility}</span>
          </span>
        </div>
        <div className="flex items-center gap-3 mt-2 md:mt-0">
          <span className="text-[10px] text-[var(--text-muted)] font-mono">
            Live {secondsSinceRefresh}s ago
          </span>
          <Button variant="ghost" size="sm" onClick={handleManualRefresh} className="p-1 h-auto hover:bg-[var(--bg-elevated)]">
            Refresh
          </Button>
        </div>
      </div>

      {/* ====== THE 6 EXECUTIVE SECTIONS ====== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Section 1: What happened overnight? */}
        <Card className="bg-black/35 border-[var(--border-subtle)] hover:border-[var(--text-muted)] transition-colors duration-200">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                1. Overnight Status
              </span>
              <Badge variant="success">
                Processed
              </Badge>
            </div>
            <p className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
              "What happened overnight?"
            </p>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              {brief.overnight_summary}
            </p>
          </CardContent>
        </Card>

        {/* Section 2: What requires my attention now? */}
        <Card className="bg-black/35 border-[var(--border-subtle)] hover:border-[var(--text-muted)] transition-colors duration-200">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                2. Immediate Attention
              </span>
              <Badge variant={attention.length > 1 || attention[0]?.type !== "INFO" ? "danger" : "success"}>
                {attention.length > 1 || attention[0]?.type !== "INFO" ? "Alerts" : "Nominal"}
              </Badge>
            </div>
            <p className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
              "What requires my attention now?"
            </p>
            <div className="space-y-1">
              {attention.map((item: any, i: number) => (
                <div key={i} className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  <span className="font-semibold" style={{ color: getStatusColor(item.type === "RISK" ? "CRITICAL" : "EXCELLENT") }}>
                    {item.type}:
                  </span>{" "}
                  {item.message}
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    → Action: {item.action}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Section 3: What is my portfolio risk today? */}
        <Card className="bg-black/35 border-[var(--border-subtle)] hover:border-[var(--text-muted)] transition-colors duration-200">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                3. Risk Profiler
              </span>
              <span className="text-sm font-bold font-mono" style={{ color: getStatusColor(portfolio.status) }}>
                {portfolio.score}/100 ({portfolio.status})
              </span>
            </div>
            <p className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
              "What is my portfolio risk today?"
            </p>

            <div className="space-y-1 text-xs text-[var(--text-secondary)]">
              {portfolio.contributors.map((c: string, idx: number) => (
                <div key={idx} className="flex items-start gap-1 text-[11px] leading-relaxed">
                  <span>{c}</span>
                </div>
              ))}
              <div className="pt-1 text-[10px] text-[var(--accent-yellow)] font-mono border-t border-[var(--border-subtle)] mt-1">
                Recommendation: {portfolio.recommended_action}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Section 4: What are my best opportunities today? */}
        <Card className="lg:col-span-2 bg-black/35 border-[var(--border-subtle)] hover:border-[var(--text-muted)] transition-colors duration-200">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                4. Smart-Prioritized Opportunities
              </span>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">
                Formula: Dynamic Priority Ranking
              </span>
            </div>
            <p className="text-xs font-semibold text-[var(--text-primary)]">
              "What are my best opportunities today?"
            </p>

            {opportunities && opportunities.length > 0 ? (
              <div className="space-y-3">
                {opportunities.map((opp: any, index: number) => (
                  <div
                    key={opp.id || index}
                    className="p-3 rounded border border-[var(--border-subtle)] bg-black/20 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={opp.side === "LONG" ? "success" : "danger"}>
                          {opp.side}
                        </Badge>
                        <span className="font-bold text-xs text-[var(--text-primary)]">{opp.symbol}</span>
                        <span className="text-[10px] font-mono text-[var(--text-muted)]">
                          Horizon: {opp.expected_holding_horizon}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="text-[var(--text-muted)]">Confidence:</span>
                        <span className="font-semibold text-emerald-400">{opp.confidence}</span>
                        <span className="text-[var(--text-muted)]">Risk:</span>
                        <span className="font-semibold text-amber-400">{opp.risk}</span>
                      </div>
                    </div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      <span className="font-semibold text-[var(--text-primary)]">Rationale:</span>{" "}
                      {opp.why_ranked_top}
                    </div>
                    <ul className="text-[10px] text-[var(--text-muted)] space-y-0.5 list-disc pl-4">
                      {opp.supporting_evidence.map((ev: string, idx: number) => (
                        <li key={idx}>{ev}</li>
                      ))}
                    </ul>
                    <div className="text-[10px] text-emerald-400 font-semibold font-mono">
                      Action: {opp.recommended_next_action}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-muted)] italic">No active opportunities matching high-confidence priority parameters.</p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {/* Section 5: Has anything changed since yesterday? */}
          <Card className="bg-black/35 border-[var(--border-subtle)] hover:border-[var(--text-muted)] transition-colors duration-200">
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  5. Daily deltas
                </span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">24h Shift</span>
              </div>
              <p className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
                "Has anything changed since yesterday?"
              </p>
              <div className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                <div>
                  <span className="text-[var(--text-muted)]">Regime:</span>{" "}
                  {changes.regime_shift}
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">Exposure:</span>{" "}
                  {changes.active_exposure_change}
                </div>
                <div>
                  <span className="text-[var(--text-muted)]">Scanner Activity:</span>{" "}
                  {changes.new_signals_count}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Section 6: What is the single most important action I should take? */}
          <Card className="bg-black/35 border-[var(--border-subtle)] hover:border-[var(--text-muted)] transition-colors duration-200">
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                  6. Recommended Action Center
                </span>
                <Badge variant={importantAction.priority === "HIGH" ? "danger" : "default"}>
                  {importantAction.priority} Priority
                </Badge>
              </div>
              <p className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
                "What is the single most important action I should take?"
              </p>
              <div className="space-y-2">
                <div className="p-2 rounded bg-emerald-500/5 border border-emerald-500/10 text-xs space-y-1">
                  <div className="font-bold text-[var(--text-primary)]">
                    {importantAction.action}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)]">
                    {importantAction.rationale}
                  </div>
                </div>
                <Button
                  className="w-full text-xs py-1 h-8 uppercase font-semibold tracking-wider"
                  variant={importantAction.priority === "HIGH" ? "danger" : "primary"}
                  onClick={() => alert(`S12 action requested: ${importantAction.action}`)}
                >
                  Execute Action Plan
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

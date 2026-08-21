import { useEffect, useMemo, useState } from "react"
import { useOutletContext } from "react-router-dom"
import { motion } from "framer-motion"
import { useTranslation } from "react-i18next"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus } from "../types/mission"
import { NexusDashboard } from "../components/hq/NexusDashboard"
import MissionFlow from "../components/hq/MissionFlow"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"
import type { SubsystemStatus } from "../types/system"

// Merged components/imports from AIExperience
import { SignalFeed } from "../components/ai/signal-feed"
import { AnalysisDashboard } from "../components/ai/analysis-dashboard"
import ScannerOpportunitiesPanel from "../components/dashboard/ScannerOpportunitiesPanel"
import { apiFetch } from "../api/client"
import { ChartPanel } from "../components/trading/chart-panel"
import { useTerminalStore } from "../stores/terminal-store"
import type { LayoutContext } from "../components/layout/Layout"

interface LiveCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface SignalData {
  id: number;
  symbol: string;
  side: string;
  decision: string;
  confidence: number;
  final_score: number;
  price: number | null;
  created_at: string | null;
}

interface MarketData {
  price: number;
  regime: string;
  volatility: number;
  rsi: number;
}

function statusColor(status: SubsystemStatus): string {
  switch (status) {
    case "ONLINE": return "#3EDC97"
    case "DEGRADED": return "#FFB547"
    case "OFFLINE": return "#FF5D73"
    case "UNKNOWN": return "#6B7891"
  }
}

function qualityColor(q: string): string {
  switch (q) {
    case "HIGH": return "#3EDC97"
    case "MEDIUM": return "#FFB547"
    case "LOW": return "#FF5D73"
    default: return "#6B7891"
  }
}

function ProgressLine({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div className="flex items-center gap-3">
      <span
        className="font-mono shrink-0 text-right"
        style={{ fontSize: 8, color: "var(--text-muted)", width: 90, letterSpacing: "0.05em" }}
      >
        {label}
      </span>
      <div
        className="flex-1 h-px rounded-full overflow-hidden"
        style={{ backgroundColor: "var(--border-subtle)" }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span
        className="font-mono tabular-nums shrink-0"
        style={{ fontSize: 8, color, width: 28, textAlign: "right" as const }}
      >
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

export default function CommandDeck() {
  const { t } = useTranslation("commandDeck")
  const [showLoading, setShowLoading] = useState(true)
  const [signals, setSignals] = useState<SignalData[]>([])
  const [marketData, setMarketData] = useState<MarketData | null>(null)

  const {
    scanner, risk, council, portfolio, whale, market, evidence,
    ollo, aiHealth, loading,
  } = useSubsystems()

  // The system just approved and opened a real trade -- surface its chart
  // right here instead of leaving the founder to go find it on another page.
  const { openTrades } = useOutletContext<LayoutContext>()
  const setTerminalSymbol = useTerminalStore((s) => s.setSymbol)
  const activeTrade = openTrades.length > 0 ? openTrades[openTrades.length - 1] : null
  const [activeTradeCandles, setActiveTradeCandles] = useState<Candle[]>([])

  useEffect(() => {
    if (!activeTrade) {
      setActiveTradeCandles([])
      return
    }
    const baseSymbol = activeTrade.symbol.replace(/USDT$/, "")
    setTerminalSymbol(baseSymbol)
    let mounted = true
    let retryTimer: ReturnType<typeof setTimeout> | undefined

    // /market/live can 200 with {"error": ...} instead of candles during a
    // transient Hyperliquid rate-limit -- this effect only re-runs when the
    // open-trade list itself changes, so without a retry, landing on that
    // window once left the chart blank until the next trade opened/closed
    // (confirmed live 2026-08-21: a post-restart 429 burst blanked the
    // active-trade chart with no recovery). Retries with backoff instead of
    // giving up on the first failure.
    const RETRY_DELAYS_MS = [3000, 6000, 12000]

    const load = (attempt: number) => {
      apiFetch<{ candles: LiveCandle[] }>(`/market/live?symbol=${baseSymbol}&timeframe=1h&limit=100`)
        .then((res) => {
          if (!mounted) return
          if (res.candles) {
            setActiveTradeCandles(res.candles.map((c) => ({
              time: Math.floor(c.timestamp / 1000),
              open: c.open,
              high: c.high,
              low: c.low,
              close: c.close,
              volume: c.volume,
            })))
          } else if (attempt < RETRY_DELAYS_MS.length) {
            retryTimer = setTimeout(() => load(attempt + 1), RETRY_DELAYS_MS[attempt])
          } else {
            setActiveTradeCandles([])
          }
        })
        .catch(() => {
          if (!mounted) return
          if (attempt < RETRY_DELAYS_MS.length) {
            retryTimer = setTimeout(() => load(attempt + 1), RETRY_DELAYS_MS[attempt])
          } else {
            setActiveTradeCandles([])
          }
        })
    }
    load(0)

    return () => {
      mounted = false
      if (retryTimer) clearTimeout(retryTimer)
    }
  }, [activeTrade, setTerminalSymbol])

  // Fetch signals & market data for surrounding dashboard panels
  useEffect(() => {
    let mounted = true
    Promise.all([
      apiFetch<SignalData[]>("/signals?limit=10").catch(() => [] as SignalData[]),
      apiFetch<{ price?: number; regime?: string; volatility?: number; rsi?: number }>("/market").catch((): { price?: number; regime?: string; volatility?: number; rsi?: number } => ({})),
    ]).then(([sigData, mktData]) => {
      if (!mounted) return
      setSignals(Array.isArray(sigData) ? sigData : [])
      if (mktData.price) {
        setMarketData({
          price: mktData.price,
          regime: mktData.regime || "UNKNOWN",
          volatility: mktData.volatility || 0,
          rsi: mktData.rsi || 50,
        })
      }
    })
    return () => { mounted = false }
  }, [])

  const signalItems = useMemo(() => signals.slice(0, 5).map((s) => ({
    id: String(s.id),
    symbol: s.symbol,
    direction: (s.side === "BUY" || s.side === "LONG" ? "BUY" : s.side === "SELL" || s.side === "SHORT" ? "SELL" : "NEUTRAL") as "BUY" | "SELL" | "NEUTRAL",
    strength: s.final_score,
    strategy: s.decision || t("signalFeed.aiSignal"),
    price: s.price || 0,
    timestamp: s.created_at || new Date().toISOString(),
  })), [signals, t])

  const analysisItems = useMemo(() => marketData
    ? [
        { label: t("analysisLabel.trend"), value: marketData.regime, score: marketData.regime === "TREND" ? 82 : marketData.regime === "DOWNTREND" ? 25 : 50, status: (marketData.regime === "TREND" ? "bullish" : marketData.regime === "DOWNTREND" ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: t("analysisLabel.momentum"), value: marketData.rsi >= 60 ? t("analysisValue.positive") : marketData.rsi <= 40 ? t("analysisValue.negative") : t("analysisValue.neutral"), score: marketData.rsi, status: (marketData.rsi >= 60 ? "bullish" : marketData.rsi <= 40 ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: t("analysisLabel.volatility"), value: marketData.volatility >= 0.5 ? t("analysisValue.high") : marketData.volatility >= 0.2 ? t("analysisValue.moderate") : t("analysisValue.low"), score: Math.round(marketData.volatility * 100), status: "neutral" as const },
        { label: t("analysisLabel.price"), value: `$${marketData.price.toLocaleString()}`, score: 50, status: "neutral" as const },
      ]
    : [], [marketData, t])

  const decisionQuality = evidence.data?.decision_quality ?? null
  const warnings = evidence.data?.warnings ?? []
  const riskScore = risk.data?.risk_score ?? null
  const aiConnected = aiHealth.data?.ollo.connected ?? ollo.status.data?.ai_health.connected ?? null
  const aiLatency = aiHealth.data?.ollo.latency_ms ?? ollo.status.data?.ai_health.latency_ms

  const offlineCount = [scanner, risk, council, portfolio, whale, market, evidence, ollo.status, aiHealth]
    .filter((s) => s.status === "OFFLINE").length

  const missionStatus = useMemo(
    () => computeMissionStatus(riskScore, decisionQuality, aiConnected, offlineCount),
    [riskScore, decisionQuality, aiConnected, offlineCount],
  )

  const currentMission = ollo.briefing?.title || ollo.status.data?.current_mission_profile?.replace(/_/g, " ") || undefined

  const flowNodes = useMemo(() => [
    { label: "Scanner" as const, active: scanner.status === "ONLINE", color: statusColor(scanner.status) },
    { label: "Whale" as const, active: whale.status === "ONLINE", color: statusColor(whale.status) },
    { label: "Council" as const, active: council.status === "ONLINE", color: statusColor(council.status) },
    { label: "Evidence" as const, active: evidence.status === "ONLINE", color: statusColor(evidence.status) },
    { label: "Decision" as const, active: aiHealth.status === "ONLINE", color: statusColor(aiHealth.status) },
    { label: "Founder" as const, active: true, color: "#4F8CFF" },
    { label: "Action" as const, active: true, color: "#78A8FF" },
  ], [scanner.status, whale.status, council.status, evidence.status, aiHealth.status])

  const missionColor = useMemo(() => {
    switch (missionStatus) {
      case "ACTIVE": return "#3EDC97"
      case "MONITORING": return "#4F8CFF"
      case "CAUTION": return "#FFB547"
      case "CRITICAL": return "#FF5D73"
    }
  }, [missionStatus])

  const recommendation = evidence.data?.recommendation || null
  const confidence = evidence.data?.decision_confidence ?? null
  const strength = evidence.data?.evidence_strength ?? null
  const explainability = evidence.data?.explainability ?? null
  const supportingCount = evidence.data?.supporting_evidence.length ?? null
  const conflictCount = evidence.data?.contradicting_evidence.length ?? null
  const warningCount = evidence.data?.warnings.length ?? null

  // Hide loading screen after subsystems load
  useEffect(() => {
    if (!loading && showLoading) {
      const timer = setTimeout(() => setShowLoading(false), 1200)
      return () => clearTimeout(timer)
    }
  }, [loading, showLoading])

  // Safety net: apiFetch has no request timeout, so if any one of
  // useSubsystems' parallel calls hangs, `loading` never flips false and
  // the real content above would stay at opacity 0 forever, even after
  // HQLoadingScreen self-dismisses on its own independent ~1.5s timer.
  // Force the content visible after a generous ceiling regardless.
  useEffect(() => {
    const timer = setTimeout(() => setShowLoading(false), 8000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <>
      {showLoading && <HQLoadingScreen />}

      <motion.div
        className="h-full flex flex-col overflow-y-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* ====== NEXUS HERO: just the brain + voice/chat console, no cards ====== */}
        <NexusDashboard
          olloGreeting={ollo.greeting}
          olloBriefing={ollo.briefing}
          olloLoading={loading && !ollo.greeting}
          olloError={ollo.status.error}
          onEnterCommandDeck={() => document.getElementById("command-deck-panels")?.scrollIntoView({ behavior: "smooth" })}
        />

        {/* ====== MISSION STATUS STRIP ====== */}
        <div
          id="command-deck-panels"
          className="flex items-center justify-between shrink-0"
          style={{
            height: 38,
            padding: "0 20px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div className="flex items-center gap-3">
            <span
              className="text-[8px] font-semibold uppercase tracking-[0.22em]"
              style={{ color: "var(--text-primary)" }}
            >
              {t("header.title")}
            </span>
            <span
              className="text-[7px] font-mono uppercase tracking-[0.15em]"
              style={{ color: "var(--text-muted)" }}
            >
              · {t("header.founderAlpha")}
            </span>
            {currentMission && (
              <>
                <span className="text-[7px]" style={{ color: "var(--border-subtle)" }}>·</span>
                <span
                  className="text-[7px] font-mono uppercase tracking-[0.1em]"
                  style={{ color: missionColor }}
                >
                  {currentMission}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span
                className="w-1 h-1 rounded-full"
                style={{ backgroundColor: missionColor, boxShadow: `0 0 4px ${missionColor}40` }}
              />
              <span
                className="text-[8px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: missionColor }}
              >
                {t(`missionStatus.${missionStatus}`)}
              </span>
            </div>

            <span className="text-[6px]" style={{ color: "var(--border-subtle)" }}>|</span>

            <span
              className="text-[8px] font-mono tabular-nums"
              style={{ color: "var(--text-muted)" }}
            >
              {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
            </span>

            <div className="flex items-center gap-1">
              <span
                className="w-1 h-1 rounded-full"
                style={{ backgroundColor: aiConnected !== false ? "#3EDC97" : "#FF5D73" }}
              />
              <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                AI {aiConnected !== false ? (aiLatency ? `${aiLatency.toFixed(0)}ms` : t("aiStatus.ok")) : t("aiStatus.err")}
              </span>
            </div>

            {warnings.length > 0 && (
              <span className="text-[7px] font-mono" style={{ color: "#FFB547" }}>
                {t("alerts", { count: warnings.length })}
              </span>
            )}
          </div>
        </div>

        {/* ====== ACTIVE TRADE CHART — appears once the system approves and opens a real trade ====== */}
        {activeTrade && (
          <motion.div
            className="shrink-0 px-6 pt-6"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="hq-section-label">
              {t("activeTrade.title", { symbol: activeTrade.symbol, side: activeTrade.side })}
            </div>
            <div style={{ height: 340 }}>
              <ChartPanel data={activeTradeCandles} openTrades={[activeTrade]} />
            </div>
          </motion.div>
        )}

        {/* ====== CONTENT — Evidence, Mission Flow & Merged AI Experience Side Panels ====== */}
        <div className="flex-1 grid grid-cols-1 xl:grid-cols-4 gap-6 p-6">

          {/* Side Panel Left: Signal Feed + Ranked Opportunities */}
          <div className="xl:col-span-1 flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <SignalFeed signals={signalItems} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 }}
            >
              <ScannerOpportunitiesPanel />
            </motion.div>
          </div>

          {/* Centre: Recommendation / Evidence / Mission Flow */}
          <div className="xl:col-span-2 flex flex-col items-center gap-6">
            {/* Recommendation (Grounded details) */}
            {recommendation && (
              <div className="w-full max-w-xl">
                <div className="hq-section-label">{t("recommendation.title")}</div>
                <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  <p
                    className="text-xs font-semibold leading-relaxed"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {recommendation}
                  </p>
                </div>
              </div>
            )}

            {/* Evidence details */}
            {(confidence !== null || strength !== null || explainability !== null) && (
              <div className="w-full max-w-xl">
                <div className="hq-section-label">{t("evidence.title")}</div>
                <div className="space-y-3 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  {confidence !== null && (
                    <ProgressLine
                      value={confidence}
                      label={t("evidence.decisionConfidence")}
                      color={qualityColor(decisionQuality ?? "UNKNOWN")}
                    />
                  )}
                  {strength !== null && (
                    <ProgressLine value={strength} label={t("evidence.evidenceStrength")} color="#4F8CFF" />
                  )}
                  {explainability !== null && (
                    <ProgressLine value={explainability} label={t("evidence.explainability")} color="#8B5CF6" />
                  )}

                  {/* Counts */}
                  {(supportingCount !== null || conflictCount !== null || warningCount !== null) && (
                    <div className="flex items-center gap-4 mt-3 pt-2 border-t border-[var(--border-subtle)]">
                      {supportingCount !== null && (
                        <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "#3EDC97" }}>{supportingCount}</span> {t("evidence.supporting")}
                        </span>
                      )}
                      {conflictCount !== null && conflictCount > 0 && (
                        <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "#FF5D73" }}>{conflictCount}</span> {t("evidence.conflicting")}
                        </span>
                      )}
                      {warningCount !== null && warningCount > 0 && (
                        <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "#FFB547" }}>{warningCount}</span> {t("evidence.warnings")}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Mission Flow */}
            <div className="w-full max-w-xl">
              <MissionFlow nodes={flowNodes} />
            </div>
          </div>

          {/* Side Panel Right: Market Analysis */}
          <div className="xl:col-span-1 flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 }}
            >
              <AnalysisDashboard symbol="BTC/USDT" items={analysisItems} />
            </motion.div>
          </div>

        </div>

        {/* ====== BOTTOM: Subsystem Health ====== */}
        <div
          className="shrink-0"
          style={{
            padding: "8px 20px",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <SubsystemHealthBar
            scanner={scanner}
            risk={risk}
            council={council}
            portfolio={portfolio}
            whale={whale}
            market={market}
            evidence={evidence}
            olloStatus={ollo.status}
            aiHealth={aiHealth}
          />
        </div>
      </motion.div>
    </>
  )
}

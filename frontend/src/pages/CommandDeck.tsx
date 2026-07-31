import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { useSubsystems } from "../hooks/useSubsystems"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"

// Merged components/imports from AIExperience
import { SignalFeed } from "../components/ai/signal-feed"
import { AnalysisDashboard } from "../components/ai/analysis-dashboard"
import { apiFetch } from "../api/client"
import { NexusDashboard } from "../components/hq/NexusDashboard"

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

export default function CommandDeck() {
  const [showLoading, setShowLoading] = useState(true)
  const [signals, setSignals] = useState<SignalData[]>([])
  const [marketData, setMarketData] = useState<MarketData | null>(null)

  const {
    scanner, risk, council, portfolio, whale, market, evidence,
    ollo, aiHealth, loading,
  } = useSubsystems()

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
    strategy: s.decision || "AI Signal",
    price: s.price || 0,
    timestamp: s.created_at || new Date().toISOString(),
  })), [signals])

  const analysisItems = useMemo(() => marketData
    ? [
        { label: "Trend", value: marketData.regime, score: marketData.regime === "TREND" ? 82 : marketData.regime === "DOWNTREND" ? 25 : 50, status: (marketData.regime === "TREND" ? "bullish" : marketData.regime === "DOWNTREND" ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: "Momentum", value: marketData.rsi >= 60 ? "Positive" : marketData.rsi <= 40 ? "Negative" : "Neutral", score: marketData.rsi, status: (marketData.rsi >= 60 ? "bullish" : marketData.rsi <= 40 ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: "Volatility", value: marketData.volatility >= 0.5 ? "High" : marketData.volatility >= 0.2 ? "Moderate" : "Low", score: Math.round(marketData.volatility * 100), status: "neutral" as const },
        { label: "Price", value: `$${marketData.price.toLocaleString()}`, score: 50, status: "neutral" as const },
      ]
    : [], [marketData])

  // Hide loading screen after subsystems load
  useEffect(() => {
    if (!loading && showLoading) {
      const timer = setTimeout(() => setShowLoading(false), 1200)
      return () => clearTimeout(timer)
    }
  }, [loading, showLoading])

  return (
    <>
      {showLoading && <HQLoadingScreen />}

      <motion.div
        className="h-full flex flex-col"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* Render premium institutional HUD layout */}
        <NexusDashboard
          olloGreeting={ollo.greeting}
          olloBriefing={ollo.briefing}
          olloLoading={loading && !ollo.greeting}
          olloError={ollo.status.error}
        />

        {/* AI Evidence & Analysis Surfaces */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 border-t border-[var(--border-subtle)] bg-[var(--bg-base)]">
          <div className="space-y-3">
            <h2 className="text-xs font-mono tracking-widest text-cyan-400 uppercase font-bold">
              Real-time AI Signal Feed
            </h2>
            <SignalFeed signals={signalItems} />
          </div>
          <div className="space-y-3">
            <h2 className="text-xs font-mono tracking-widest text-cyan-400 uppercase font-bold">
              Technical Analysis Dashboard
            </h2>
            <AnalysisDashboard symbol="BTC/USDT" items={analysisItems} />
          </div>
        </div>

        {/* ====== BOTTOM: Subsystem Health ====== */}
        <div
          className="shrink-0"
          style={{
            padding: "8px 20px",
            borderTop: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-base)",
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

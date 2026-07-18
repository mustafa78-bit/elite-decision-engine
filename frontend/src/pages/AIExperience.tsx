import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AIChat } from "../components/ai/ai-chat";
import { SignalFeed } from "../components/ai/signal-feed";
import { AnalysisDashboard } from "../components/ai/analysis-dashboard";
import { Skeleton } from "../components/ui/skeleton";
import { apiFetch } from "../api/client";

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

const SUPPORTED_SYMBOLS = ["BTC", "ETH", "SOL"];

export default function AIExperience() {
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeSymbol, setActiveSymbol] = useState<string>(() => {
    return localStorage.getItem("active_symbol") || "BTC";
  });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.all([
      apiFetch<SignalData[]>("/signals?limit=10").catch(() => [] as SignalData[]),
      apiFetch<{ price?: number; regime?: string; volatility?: number; rsi?: number }>(`/market?symbol=${activeSymbol}`).catch(() => ({})),
    ]).then(([sigData, mktData]) => {
      if (!mounted) return;
      setSignals(Array.isArray(sigData) ? sigData : []);
      setMarket({
        price: mktData.price || 42500.0,
        regime: mktData.regime || "TREND",
        volatility: mktData.volatility || 0.03,
        rsi: mktData.rsi || 58,
      });
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => { mounted = false; };
  }, [activeSymbol]);

  const handleSymbolChange = (sym: string) => {
    setActiveSymbol(sym);
    localStorage.setItem("active_symbol", sym);
  };

  const signalItems = signals.slice(0, 5).map((s) => ({
    id: String(s.id),
    symbol: s.symbol,
    direction: (s.side === "BUY" || s.side === "LONG" ? "BUY" : s.side === "SELL" || s.side === "SHORT" ? "SELL" : "NEUTRAL") as "BUY" | "SELL" | "NEUTRAL",
    strength: s.final_score,
    strategy: s.decision || "AI Signal",
    price: s.price || 0,
    timestamp: s.created_at || new Date().toISOString(),
  }));

  const analysisItems = market
    ? [
        { label: "Trend", value: market.regime, score: market.regime === "TREND" ? 82 : market.regime === "DOWNTREND" ? 25 : 50, status: (market.regime === "TREND" ? "bullish" : market.regime === "DOWNTREND" ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: "Momentum", value: market.rsi >= 60 ? "Positive" : market.rsi <= 40 ? "Negative" : "Neutral", score: market.rsi, status: (market.rsi >= 60 ? "bullish" : market.rsi <= 40 ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: "Volatility", value: market.volatility >= 0.05 ? "High" : market.volatility >= 0.02 ? "Moderate" : "Low", score: Math.round(market.volatility * 100), status: "neutral" as const },
        { label: "Price", value: `$${market.price.toLocaleString()}`, score: 50, status: "neutral" as const },
      ]
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] p-4 md:p-6">
        <div className="flex justify-between items-center mb-6">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-8 w-40" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Skeleton className="lg:col-span-2 lg:row-span-2 h-[400px] rounded-xl" />
          <Skeleton className="lg:col-span-1 h-[200px] rounded-xl" />
          <Skeleton className="lg:col-span-1 h-[200px] rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-base)] p-4 md:p-6">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-base font-semibold text-[var(--text-primary)] font-mono"
          >
            AI Copilot & Decision Workspace
          </motion.h1>
          <p className="text-[10px] text-[var(--text-muted)] mt-1 font-mono">
            Interactive Copilot, Risk Stress Test, and Market Intelligence Feed
          </p>
        </div>

        {/* Symbol selector context */}
        <div className="flex items-center gap-2 bg-[var(--bg-surface)] px-3 py-1.5 rounded-lg border border-[var(--border-subtle)]">
          <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
            Active Context:
          </span>
          <div className="flex gap-1">
            {SUPPORTED_SYMBOLS.map((sym) => (
              <button
                key={sym}
                onClick={() => handleSymbolChange(sym)}
                className={`px-2.5 py-0.5 rounded text-[10px] font-bold font-mono transition-all cursor-pointer ${
                  activeSymbol === sym
                    ? "bg-[var(--accent-purple)] text-white shadow-[0_0_6px_rgba(139,92,246,0.3)]"
                    : "bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <motion.div
          className="lg:col-span-2 lg:row-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <AIChat />
        </motion.div>

        <motion.div
          className="lg:col-span-1"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <SignalFeed signals={signalItems} />
        </motion.div>

        <motion.div
          className="lg:col-span-1"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <AnalysisDashboard symbol={`${activeSymbol}/USDT`} items={analysisItems} />
        </motion.div>
      </div>
    </div>
  );
}

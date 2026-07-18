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

export default function AIExperience() {
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      apiFetch<SignalData[]>("/signals?limit=10").catch(() => [] as SignalData[]),
      apiFetch<{ price?: number; regime?: string; volatility?: number; rsi?: number }>("/market").catch(() => ({} as { price?: number; regime?: string; volatility?: number; rsi?: number })),
    ]).then(([sigData, mktData]) => {
      if (!mounted) return;
      setSignals(Array.isArray(sigData) ? sigData : []);
      if (mktData && mktData.price) {
        setMarket({
          price: mktData.price,
          regime: mktData.regime || "UNKNOWN",
          volatility: mktData.volatility || 0,
          rsi: mktData.rsi || 50,
        });
      }
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => { mounted = false; };
  }, []);

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
        { label: "Volatility", value: market.volatility >= 0.5 ? "High" : market.volatility >= 0.2 ? "Moderate" : "Low", score: Math.round(market.volatility * 100), status: "neutral" as const },
        { label: "Price", value: `$${market.price.toLocaleString()}`, score: 50, status: "neutral" as const },
      ]
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] p-4 md:p-6">
        <Skeleton className="h-6 w-32 mb-4" />
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
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-sm font-medium text-[var(--text-primary)] mb-4"
      >
        AI Experience
      </motion.h1>

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
          <AnalysisDashboard symbol="BTC/USDT" items={analysisItems} />
        </motion.div>
      </div>
    </div>
  );
}

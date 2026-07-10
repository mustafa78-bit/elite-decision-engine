import { motion } from "framer-motion";
import { AIChat } from "../components/ai/ai-chat";
import { SignalFeed } from "../components/ai/signal-feed";
import { AnalysisDashboard } from "../components/ai/analysis-dashboard";

const sampleSignals = [
  { id: "1", symbol: "BTC/USDT", direction: "BUY" as const, strength: 8.2, strategy: "Momentum Cross", price: 42890, timestamp: new Date().toISOString() },
  { id: "2", symbol: "ETH/USDT", direction: "BUY" as const, strength: 7.5, strategy: "Support Bounce", price: 2350, timestamp: new Date().toISOString() },
  { id: "3", symbol: "SOL/USDT", direction: "SELL" as const, strength: 6.8, strategy: "Resistance Reject", price: 138, timestamp: new Date().toISOString() },
  { id: "4", symbol: "LINK/USDT", direction: "BUY" as const, strength: 6.2, strategy: "Volume Spike", price: 18.45, timestamp: new Date().toISOString() },
  { id: "5", symbol: "AVAX/USDT", direction: "NEUTRAL" as const, strength: 4.0, strategy: "Range Bound", price: 35.20, timestamp: new Date().toISOString() },
];

const sampleAnalysis = [
  { label: "Trend", value: "Strong Bullish", score: 82, status: "bullish" as const },
  { label: "Momentum", value: "Positive", score: 68, status: "bullish" as const },
  { label: "Volatility", value: "Moderate", score: 45, status: "neutral" as const },
  { label: "Support", value: "$41,800", score: 76, status: "bullish" as const },
  { label: "Resistance", value: "$43,500", score: 35, status: "bearish" as const },
];

export default function AIExperience() {
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
          <SignalFeed signals={sampleSignals} />
        </motion.div>

        <motion.div
          className="lg:col-span-1"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <AnalysisDashboard symbol="BTC/USDT" items={sampleAnalysis} />
        </motion.div>
      </div>
    </div>
  );
}

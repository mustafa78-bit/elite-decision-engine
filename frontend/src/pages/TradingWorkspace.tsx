import { motion } from "framer-motion";
import { SymbolSearch } from "../components/trading/symbol-search";
import { ChartPanel } from "../components/trading/chart-panel";
import { OrderPanel } from "../components/trading/order-panel";

const sampleCandles = Array.from({ length: 100 }, (_, i) => {
  const base = 42000 + Math.sin(i * 0.1) * 2000 + (i * 15);
  const open = base + (Math.random() - 0.5) * 200;
  const close = base + (Math.random() - 0.5) * 200;
  const high = Math.max(open, close) + Math.random() * 150;
  const low = Math.min(open, close) - Math.random() * 150;
  return {
    time: Math.floor(Date.now() / 1000) - (100 - i) * 3600,
    open,
    high,
    low,
    close,
    volume: Math.random() * 1000 + 500,
  };
});

export default function TradingWorkspace() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4 mb-4"
      >
        <h1 className="text-sm font-medium text-[var(--text-primary)]">
          Trading Workspace
        </h1>
        <SymbolSearch />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <motion.div
          className="lg:col-span-3"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ChartPanel data={sampleCandles} />
        </motion.div>

        <motion.div
          className="lg:col-span-1"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <OrderPanel />
        </motion.div>
      </div>
    </div>
  );
}

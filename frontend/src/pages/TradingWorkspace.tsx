import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { SymbolSearch } from "../components/trading/symbol-search";
import { ChartPanel } from "../components/trading/chart-panel";
import { OrderPanel } from "../components/trading/order-panel";
import { Skeleton } from "../components/ui/skeleton";
import { apiFetch } from "../api/client";

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

export default function TradingWorkspace() {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    apiFetch<{ symbol: string; candles: LiveCandle[] }>("/market/live?symbol=BTC&timeframe=1h&limit=100")
      .then((res) => {
        if (mounted && res.candles) {
          setCandles(res.candles.map((c) => ({
            time: Math.floor(c.timestamp / 1000),
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            volume: c.volume,
          })));
        }
      })
      .catch(() => { if (mounted) setCandles([]); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

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
          {loading ? (
            <Skeleton className="h-[400px] w-full rounded-xl" />
          ) : (
            <ChartPanel data={candles} />
          )}
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

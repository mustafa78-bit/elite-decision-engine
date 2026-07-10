import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Indicator {
  id: string;
  name: string;
  category: string;
  enabled: boolean;
}

interface TVIndicatorPaletteProps {
  indicators?: Indicator[];
  onToggle?: (id: string, enabled: boolean) => void;
}

const defaultIndicators: Indicator[] = [
  { id: "ema-20", name: "EMA 20", category: "Trend", enabled: true },
  { id: "ema-50", name: "EMA 50", category: "Trend", enabled: false },
  { id: "ema-200", name: "EMA 200", category: "Trend", enabled: false },
  { id: "sma-20", name: "SMA 20", category: "Trend", enabled: false },
  { id: "bb-20", name: "Bollinger Bands", category: "Volatility", enabled: false },
  { id: "rsi-14", name: "RSI 14", category: "Momentum", enabled: true },
  { id: "macd", name: "MACD", category: "Momentum", enabled: false },
  { id: "vwap", name: "VWAP", category: "Volume", enabled: false },
  { id: "volume", name: "Volume", category: "Volume", enabled: true },
];

const categories = ["Trend", "Momentum", "Volatility", "Volume"];

export function TVIndicatorPalette({
  indicators = defaultIndicators,
  onToggle,
}: TVIndicatorPaletteProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="px-2 py-1 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
      >
        Indicators ({indicators.filter((i) => i.enabled).length})
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="absolute top-full right-0 mt-1 w-56 z-50 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-xl shadow-2xl p-2"
          >
            {categories.map((cat) => {
              const catIndicators = indicators.filter((i) => i.category === cat);
              if (catIndicators.length === 0) return null;
              return (
                <div key={cat} className="mb-2 last:mb-0">
                  <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1 mb-1">
                    {cat}
                  </div>
                  {catIndicators.map((ind) => (
                    <label
                      key={ind.id}
                      className="flex items-center gap-2 px-2 py-1 rounded-lg cursor-pointer hover:bg-[var(--bg-base)] transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={ind.enabled}
                        onChange={(e) => onToggle?.(ind.id, e.target.checked)}
                        className="rounded border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]/30"
                      />
                      <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                        {ind.name}
                      </span>
                    </label>
                  ))}
                </div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

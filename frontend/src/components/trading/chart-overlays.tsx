import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../ui/button";
interface OverlayConfig {
  id: string;
  name: string;
  category: string;
  icon: string;
  enabled: boolean;
}

const availableOverlays: OverlayConfig[] = [
  { id: "regime", name: "Market Regime", category: "Analysis", icon: "◆", enabled: false },
  { id: "heatmap", name: "Volume Heatmap", category: "Volume", icon: "▨", enabled: false },
  { id: "support-resistance", name: "Support/Resistance", category: "Analysis", icon: "━", enabled: true },
  { id: "vwap", name: "VWAP", category: "Volume", icon: "∼", enabled: false },
  { id: "trendlines", name: "Trend Lines", category: "Drawing", icon: "╱", enabled: false },
  { id: "fibonacci", name: "Fibonacci", category: "Drawing", icon: "≋", enabled: false },
];

const categories = ["Analysis", "Volume", "Drawing"];

export function ChartOverlays() {
  const [open, setOpen] = useState(false);
  const [overlays, setOverlays] = useState(availableOverlays);

  const toggleOverlay = (id: string) => {
    setOverlays((prev) =>
      prev.map((o) => (o.id === id ? { ...o, enabled: !o.enabled } : o)),
    );
  };

  return (
    <div className="relative">
      <Button
        variant="glass"
        size="sm"
        onClick={() => setOpen(!open)}
        className="text-[10px]"
      >
        Overlays ({overlays.filter((o) => o.enabled).length})
      </Button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="absolute top-full right-0 mt-1 w-56 z-50 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-xl shadow-2xl p-2"
          >
            <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1 mb-2">
              Chart Overlays
            </div>
            {categories.map((cat) => {
              const catOverlays = overlays.filter((o) => o.category === cat);
              if (catOverlays.length === 0) return null;
              return (
                <div key={cat} className="mb-2 last:mb-0">
                  <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1 mb-1">
                    {cat}
                  </div>
                  {catOverlays.map((o) => (
                    <label
                      key={o.id}
                      className="flex items-center gap-2 px-2 py-1 rounded-lg cursor-pointer hover:bg-[var(--bg-base)] transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={o.enabled}
                        onChange={() => toggleOverlay(o.id)}
                        className="rounded border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]/30"
                      />
                      <span className="text-[10px]">{o.icon}</span>
                      <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                        {o.name}
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

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../ui/button";
import { useWorkspaceStore } from "../../stores/workspace-store";

interface PresetLayout {
  id: string;
  name: string;
  description: string;
  icon: string;
  panels: Array<{ type: string; title: string; x: number; y: number; w: number; h: number }>;
}

const presets: PresetLayout[] = [
  {
    id: "trading",
    name: "Trading",
    description: "Chart + order panel + watchlist",
    icon: "📊",
    panels: [
      { type: "chart", title: "Chart", x: 0, y: 0, w: 600, h: 400 },
      { type: "order", title: "Order Panel", x: 620, y: 0, w: 300, h: 400 },
      { type: "watchlist", title: "Watchlist", x: 0, y: 420, w: 920, h: 200 },
    ],
  },
  {
    id: "analytics",
    name: "Analytics",
    description: "Full analysis workspace",
    icon: "📈",
    panels: [
      { type: "kpi", title: "KPI Strip", x: 0, y: 0, w: 1200, h: 100 },
      { type: "portfolio", title: "Portfolio", x: 0, y: 120, w: 400, h: 300 },
      { type: "signals", title: "Signals", x: 420, y: 120, w: 380, h: 300 },
      { type: "risk", title: "Risk", x: 820, y: 120, w: 380, h: 300 },
      { type: "chart", title: "Chart", x: 0, y: 440, w: 800, h: 350 },
      { type: "intelligence", title: "Intelligence", x: 820, y: 440, w: 380, h: 350 },
    ],
  },
  {
    id: "monitoring",
    name: "Monitoring",
    description: "System health dashboard",
    icon: "🔍",
    panels: [
      { type: "health", title: "Health", x: 0, y: 0, w: 400, h: 200 },
      { type: "latency", title: "Latency", x: 420, y: 0, w: 400, h: 200 },
      { type: "errors", title: "Errors", x: 840, y: 0, w: 360, h: 200 },
      { type: "notifications", title: "Notifications", x: 0, y: 220, w: 600, h: 300 },
      { type: "timeline", title: "Timeline", x: 620, y: 220, w: 580, h: 300 },
    ],
  },
  {
    id: "ai",
    name: "AI Workspace",
    description: "AI analysis center",
    icon: "🤖",
    panels: [
      { type: "chat", title: "AI Chat", x: 0, y: 0, w: 400, h: 500 },
      { type: "signals", title: "Signals", x: 420, y: 0, w: 400, h: 250 },
      { type: "sentiment", title: "Sentiment", x: 840, y: 0, w: 360, h: 250 },
      { type: "analysis", title: "Analysis", x: 420, y: 270, w: 400, h: 230 },
      { type: "predictions", title: "Predictions", x: 840, y: 270, w: 360, h: 230 },
    ],
  },
  {
    id: "minimal",
    name: "Minimal",
    description: "Clean single chart",
    icon: "⏺",
    panels: [
      { type: "chart", title: "Chart", x: 0, y: 0, w: 920, h: 500 },
    ],
  },
];

export function WorkspacePresets() {
  const [open, setOpen] = useState(false);
  const { addPanel, removePanel, panels } = useWorkspaceStore();

  const handleApply = (preset: PresetLayout) => {
    panels.forEach((p) => removePanel(p.id));
    preset.panels.forEach((p) => {
      addPanel({
        id: `${preset.id}-${p.type}-${Date.now()}`,
        type: p.type,
        title: p.title,
        x: p.x,
        y: p.y,
        w: p.w,
        h: p.h,
        minimized: false,
      });
    });
    setOpen(false);
  };

  return (
    <div className="relative">
      <Button
        variant="glass"
        size="sm"
        onClick={() => setOpen(!open)}
        className="text-[12px]"
      >
        Presets
      </Button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="absolute top-full left-0 mt-1 w-72 z-50 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-xl shadow-2xl p-2"
          >
            <div className="text-[12px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1 mb-2">
              Workspace Presets
            </div>
            <div className="space-y-1">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handleApply(preset)}
                  className="w-full flex items-start gap-2 px-2 py-2 rounded-lg hover:bg-[var(--bg-base)] transition-colors text-left"
                >
                  <span className="text-sm mt-0.5">{preset.icon}</span>
                  <div>
                    <div className="text-[12px] font-mono font-medium text-[var(--text-primary)]">
                      {preset.name}
                    </div>
                    <div className="text-[12px] text-[var(--text-muted)]">
                      {preset.description} · {preset.panels.length} panels
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

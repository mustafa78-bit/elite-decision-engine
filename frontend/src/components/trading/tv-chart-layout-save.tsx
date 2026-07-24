import { useState } from "react";
import { Button } from "../ui/button";
import { useWorkspaceStore } from "../../stores/workspace-store";

interface ChartLayout {
  id: string;
  name: string;
  timeframe: string;
  indicators: string[];
  comparisonSymbols: string[];
}

interface TVChartLayoutSaveProps {
  currentTimeframe?: string;
  currentIndicators?: string[];
  currentComparison?: string[];
}

export function TVChartLayoutSave({
  currentTimeframe = "1h",
  currentIndicators = [],
  currentComparison = [],
}: TVChartLayoutSaveProps) {
  const [savedLayouts, setSavedLayouts] = useState<ChartLayout[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("tv-layouts") || "[]");
    } catch {
      return [];
    }
  });
  const [name, setName] = useState("");
  const [showSave, setShowSave] = useState(false);
  const { addPanel } = useWorkspaceStore();

  const handleSave = () => {
    if (!name.trim()) return;
    const layout: ChartLayout = {
      id: Date.now().toString(),
      name: name.trim(),
      timeframe: currentTimeframe,
      indicators: currentIndicators,
      comparisonSymbols: currentComparison,
    };
    const updated = [...savedLayouts, layout];
    setSavedLayouts(updated);
    localStorage.setItem("tv-layouts", JSON.stringify(updated));
    setName("");
    setShowSave(false);
  };

  const handleLoad = (layout: ChartLayout) => {
    addPanel({
      id: `layout-${layout.id}`,
      type: "chart-layout",
      title: "Chart Layout",
      x: 100,
      y: 100,
      w: 600,
      h: 400,
      minimized: false,
    });
  };

  const handleDelete = (id: string) => {
    const updated = savedLayouts.filter((l) => l.id !== id);
    setSavedLayouts(updated);
    localStorage.setItem("tv-layouts", JSON.stringify(updated));
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Button
          variant="glass"
          size="sm"
          onClick={() => setShowSave(!showSave)}
          className="text-[12px]"
        >
          Save Layout
        </Button>
      </div>
      {showSave && (
        <div className="flex gap-2">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSave()}
            placeholder="Layout name..."
            className="flex-1 bg-[var(--bg-base)] rounded-lg px-2 py-1 text-[12px] font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-default)] focus:outline-none focus:border-[var(--accent-blue)]"
          />
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={!name.trim()}
            className="text-[12px]"
          >
            Save
          </Button>
        </div>
      )}
      {savedLayouts.length > 0 && (
        <div className="space-y-1">
          {savedLayouts.map((layout) => (
            <div
              key={layout.id}
              className="flex items-center justify-between px-2 py-1 rounded-lg bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)]"
            >
              <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                {layout.name}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleLoad(layout)}
                  className="text-[12px] font-mono text-[var(--accent-blue)] hover:text-[var(--accent-blue)]/80"
                >
                  Load
                </button>
                <button
                  onClick={() => handleDelete(layout.id)}
                  className="text-[12px] font-mono text-[var(--accent-red)] hover:text-[var(--accent-red)]/80"
                >
                  Del
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

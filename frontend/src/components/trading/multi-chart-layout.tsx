import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { ChartPanel } from "./chart-panel";
import { TVTimeframeSelector } from "./tv-timeframe-selector";
import { cn } from "../../lib/utils";

type ChartLayout = "single" | "dual" | "quad" | "grid3";

interface ChartInstance {
  id: string;
  symbol: string;
  timeframe: string;
  linked: boolean;
}

const layoutGrids: Record<ChartLayout, string> = {
  single: "grid-cols-1 grid-rows-1",
  dual: "grid-cols-2 grid-rows-1",
  quad: "grid-cols-2 grid-rows-2",
  grid3: "grid-cols-3 grid-rows-1",
};

export function MultiChartLayout() {
  const [layout, setLayout] = useState<ChartLayout>("single");
  const [charts, setCharts] = useState<ChartInstance[]>([
    { id: "c1", symbol: "BTC/USDT", timeframe: "1h", linked: true },
  ]);
  const [linkCharts, setLinkCharts] = useState(true);

  const addChart = useCallback(() => {
    if (charts.length >= 4) return;
    const symbols = ["ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT"];
    const newChart: ChartInstance = {
      id: `c${Date.now()}`,
      symbol: symbols[charts.length % symbols.length],
      timeframe: "1h",
      linked: linkCharts,
    };
    setCharts((prev) => [...prev, newChart]);
    if (charts.length + 1 === 2) setLayout("dual");
    else if (charts.length + 1 === 3) setLayout("quad");
    else if (charts.length + 1 >= 4) setLayout("quad");
  }, [charts.length, linkCharts]);

  const removeChart = useCallback((id: string) => {
    setCharts((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (next.length === 0) {
        return [{ id: "c1", symbol: "BTC/USDT", timeframe: "1h", linked: true }];
      }
      if (next.length === 1) setLayout("single");
      if (next.length === 2) setLayout("dual");
      return next;
    });
  }, []);

  const setTimeframe = useCallback((tf: string) => {
    setCharts((prev) =>
      prev.map((c) => (c.linked || prev.length === 1 ? { ...c, timeframe: tf } : c)),
    );
  }, []);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Charts</CardTitle>
          <div className="flex items-center gap-2">
            {charts.length > 0 && (
              <TVTimeframeSelector
                selected={charts[0].timeframe as any}
                onChange={(tf) => setTimeframe(tf)}
              />
            )}
            <div className="flex gap-0.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] p-0.5">
              {(["single", "dual", "quad"] as ChartLayout[]).map((l) => (
                <button
                  key={l}
                  onClick={() => setLayout(l)}
                  className={cn(
                    "px-1.5 py-1 text-[9px] font-mono rounded-md transition-all",
                    layout === l
                      ? "bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
                  )}
                >
                  {l === "single" ? "1" : l === "dual" ? "2" : "4"}
                </button>
              ))}
            </div>
            <label className="flex items-center gap-1 text-[9px] font-mono text-[var(--text-muted)] cursor-pointer">
              <input
                type="checkbox"
                checked={linkCharts}
                onChange={() => setLinkCharts(!linkCharts)}
                className="rounded border-[var(--border-default)] bg-[var(--bg-base)]"
              />
              Link
            </label>
            <Button variant="glass" size="sm" onClick={addChart} disabled={charts.length >= 4} className="text-[10px]">
              + Chart
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 p-2">
        <div
          className={cn(
            "h-full gap-1",
            layoutGrids[layout],
            layout === "grid3" ? "grid" : "grid",
          )}
          style={{
            display: "grid",
            gridTemplateColumns:
              layout === "single"
                ? "1fr"
                : layout === "dual"
                  ? "1fr 1fr"
                  : layout === "quad"
                    ? "1fr 1fr"
                    : "1fr 1fr 1fr",
            gridTemplateRows:
              layout === "single"
                ? "1fr"
                : layout === "dual"
                  ? "1fr"
                  : layout === "quad"
                    ? "1fr 1fr"
                    : "1fr",
          }}
        >
          {charts.slice(0, layout === "quad" ? 4 : layout === "dual" ? 2 : 1).map((chart) => (
            <div key={chart.id} className="relative rounded-lg overflow-hidden border border-[var(--border-subtle)]">
              <div className="absolute top-1 left-2 z-10 flex items-center gap-2">
                <span className="text-[9px] font-mono text-[var(--text-muted)]">
                  {chart.symbol}
                </span>
                <span className="text-[8px] font-mono text-[var(--text-muted)]">
                  {chart.timeframe}
                </span>
              </div>
              <ChartPanel data={[]} />
              {charts.length > 1 && (
                <button
                  onClick={() => removeChart(chart.id)}
                  className="absolute top-1 right-2 z-10 w-3.5 h-3.5 rounded-full bg-[var(--bg-base)] border border-[var(--border-subtle)] flex items-center justify-center text-[7px] text-[var(--text-muted)] hover:text-[var(--accent-red)]"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

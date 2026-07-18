import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";

interface HeatmapCell {
  symbol: string;
  change: number;
}

const defaultCells: HeatmapCell[] = [
  { symbol: "BTC", change: 1.85 },
  { symbol: "ETH", change: -0.65 },
  { symbol: "SOL", change: 3.12 },
  { symbol: "LINK", change: -1.40 },
  { symbol: "AVAX", change: 0.85 },
  { symbol: "DOT", change: -2.15 },
  { symbol: "UNI", change: 4.50 },
  { symbol: "AAVE", change: 5.20 },
];

interface HeatmapWidgetProps {
  cells?: HeatmapCell[];
}

export function HeatmapWidget({ cells = defaultCells }: HeatmapWidgetProps) {
  const navigate = useNavigate();

  const maxAbs = Math.max(
    ...cells.map((c) => Math.abs(c.change)),
    0.001,
  );

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/market")}
      role="region"
      aria-label="Market Heatmap"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/market");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Market Heatmap</span>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          <div className="grid grid-cols-4 gap-1 max-h-[160px] overflow-y-auto">
            {cells.map((cell) => {
              const intensity = Math.abs(cell.change) / maxAbs;
              const isPositive = cell.change >= 0;

              return (
                <div
                  key={cell.symbol}
                  className="p-1.5 rounded text-center transition-all hover:scale-[1.03] select-none"
                  style={{
                    backgroundColor: isPositive
                      ? `rgba(34, 197, 94, ${0.12 + intensity * 0.45})`
                      : `rgba(239, 68, 68, ${0.12 + intensity * 0.45})`,
                    border: `1px solid ${
                      isPositive
                        ? `rgba(34, 197, 94, ${0.2 + intensity * 0.3})`
                        : `rgba(239, 68, 68, ${0.2 + intensity * 0.3})`
                    }`,
                  }}
                >
                  <div className="text-[9px] font-mono font-bold text-[var(--text-primary)]">
                    {cell.symbol}
                  </div>
                  <div
                    className={`text-[9px] font-mono font-semibold tabular-nums ${
                      isPositive
                        ? "text-[var(--accent-green)]"
                        : "text-[var(--accent-red)]"
                    }`}
                  >
                    {isPositive ? "+" : ""}
                    {cell.change.toFixed(1)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Sort: Market Capitalization</span>
          <span className="text-[var(--accent-green)]">Bullish Squeeze (6/8 Up)</span>
        </div>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface HeatmapCell {
  symbol: string;
  change: number;
  value: number;
}

interface HeatmapWidgetProps {
  cells?: HeatmapCell[];
}

export function HeatmapWidget({ cells = [] }: HeatmapWidgetProps) {
  if (cells.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No heatmap data
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxAbs = Math.max(
    ...cells.map((c) => Math.abs(c.change)),
    0.001,
  );

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Heatmap</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-1">
          {cells.slice(0, 16).map((cell) => {
            const intensity = Math.abs(cell.change) / maxAbs;
            const isPositive = cell.change >= 0;

            return (
              <div
                key={cell.symbol}
                className="p-2 rounded-lg text-center transition-all hover:scale-105"
                style={{
                  backgroundColor: isPositive
                    ? `rgba(34, 197, 94, ${0.1 + intensity * 0.4})`
                    : `rgba(239, 68, 68, ${0.1 + intensity * 0.4})`,
                  border: `1px solid ${
                    isPositive
                      ? `rgba(34, 197, 94, ${0.15 + intensity * 0.3})`
                      : `rgba(239, 68, 68, ${0.15 + intensity * 0.3})`
                  }`,
                }}
              >
                <div className="text-[12px] font-mono font-medium text-[var(--text-primary)]">
                  {cell.symbol}
                </div>
                <div
                  className={`text-[12px] font-mono tabular-nums ${
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
      </CardContent>
    </Card>
  );
}

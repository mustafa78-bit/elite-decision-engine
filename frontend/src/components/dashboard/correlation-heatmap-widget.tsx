import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface CorrelationHeatmapWidgetProps {
  symbols?: string[];
  data?: Record<string, Record<string, number>>;
}

export function CorrelationHeatmapWidget({
  symbols = [],
  data = {},
}: CorrelationHeatmapWidgetProps) {
  if (symbols.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Correlation Heatmap</CardTitle></CardHeader>
        <CardContent>
          <div className="text-sm text-[var(--text-muted)] text-center py-4">No data</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Correlation Heatmap</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-px" style={{
          gridTemplateColumns: `40px repeat(${symbols.length}, 1fr)`,
        }}>
          <div />
          {symbols.map((s) => (
            <div key={s} className="text-[11px] font-mono text-[var(--text-muted)] text-center p-1">
              {s}
            </div>
          ))}
          {symbols.map((row) => [
            <div key={`label-${row}`} className="text-[11px] font-mono text-[var(--text-muted)] p-1">
              {row}
            </div>,
            ...symbols.map((col) => {
              const val = data[row]?.[col] ?? (row === col ? 1 : 0);
              const isPositive = val >= 0;
              const intensity = Math.abs(val);
              return (
                <div
                  key={`${row}-${col}`}
                  className="text-[12px] font-mono tabular-nums text-center p-1.5 rounded"
                  style={{
                    backgroundColor: row === col
                      ? "transparent"
                      : isPositive
                        ? `rgba(34, 197, 94, ${intensity * 0.6})`
                        : `rgba(239, 68, 68, ${intensity * 0.6})`,
                    color: intensity > 0.5 ? "#fff" : "var(--text-muted)",
                  }}
                >
                  {val.toFixed(2)}
                </div>
              );
            }),
          ])}
        </div>
      </CardContent>
    </Card>
  );
}

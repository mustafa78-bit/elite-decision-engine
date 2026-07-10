import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface CorrelationMatrixWidgetProps {
  symbols?: string[];
  matrix?: Record<string, Record<string, number>>;
}

export function CorrelationMatrixWidget({
  symbols = ["BTC", "ETH", "SOL", "LINK", "AVAX"],
  matrix = {},
}: CorrelationMatrixWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Correlation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-[10px] font-mono">
            <thead>
              <tr>
                <th className="p-1 text-left text-[var(--text-muted)]" />
                {symbols.map((s) => (
                  <th key={s} className="p-1 text-center text-[var(--text-muted)]">
                    {s}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {symbols.map((row, _i) => (
                <tr key={row}>
                  <td className="p-1 font-medium text-[var(--text-primary)]">{row}</td>
                  {symbols.map((col) => {
                    const val = matrix[row]?.[col] ?? (row === col ? 1 : 0);
                    const isPositive = val >= 0;
                    const intensity = Math.abs(val);
                    return (
                      <td
                        key={col}
                        className="p-1 text-center tabular-nums rounded"
                        style={{
                          backgroundColor: row === col
                            ? "transparent"
                            : isPositive
                              ? `rgba(34, 197, 94, ${intensity * 0.5})`
                              : `rgba(239, 68, 68, ${intensity * 0.5})`,
                          color: row === col ? "var(--text-muted)" : "var(--text-primary)",
                        }}
                      >
                        {val.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

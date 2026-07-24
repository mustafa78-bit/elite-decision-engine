import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface MacroIndicator {
  name: string;
  value: string;
  change: number;
  status: "bullish" | "bearish" | "neutral";
}

interface MacroWidgetProps {
  indicators?: MacroIndicator[];
}

export function MacroWidget({
  indicators = [
    { name: "US DXY", value: "104.2", change: -0.3, status: "bearish" },
    { name: "S&P 500", value: "5,234", change: 0.8, status: "bullish" },
    { name: "US 10Y", value: "4.32%", change: -0.02, status: "bullish" },
    { name: "VIX", value: "14.2", change: -1.1, status: "bullish" },
    { name: "Gold", value: "$2,345", change: 0.5, status: "bullish" },
  ],
}: MacroWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Macro Overview
          <Badge variant="info">Live</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {indicators.map((ind) => (
            <div
              key={ind.name}
              className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]"
            >
              <div className="flex items-center gap-2">
                <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                  {ind.name}
                </span>
                <span className="text-[12px] font-mono tabular-nums text-[var(--text-primary)]">
                  {ind.value}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`text-[12px] font-mono tabular-nums ${ind.change >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {ind.change >= 0 ? "+" : ""}{ind.change}%
                </span>
                <Badge variant={ind.status === "bullish" ? "success" : ind.status === "bearish" ? "danger" : "warning"}>
                  {ind.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

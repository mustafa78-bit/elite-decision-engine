import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

import { formatUSD } from "../../lib/utils";

interface DailyPnLWidgetProps {
  dailyPnl?: number;
  dailyPct?: number;
  totalPnl?: number;
}

export function DailyPnLWidget({
  dailyPnl = 0,
  dailyPct = 0,
  totalPnl = 0,
}: DailyPnLWidgetProps) {
  const isPositive = dailyPnl >= 0;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Daily P&L</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              isPositive
                ? "bg-[var(--accent-green)]/10"
                : "bg-[var(--accent-red)]/10"
            }`}
          >
            {isPositive ? (
              <svg className="w-5 h-5 text-[var(--accent-green)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-[var(--accent-red)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />
              </svg>
            )}
          </div>
          <div>
            <div
              className={`text-xl font-mono font-bold tabular-nums ${
                isPositive
                  ? "text-[var(--accent-green)]"
                  : "text-[var(--accent-red)]"
              }`}
            >
              {isPositive ? "+" : ""}
              {formatUSD(dailyPnl)}
            </div>
            <div
              className={`text-xs font-mono ${
                isPositive
                  ? "text-[var(--accent-green)]/70"
                  : "text-[var(--accent-red)]/70"
              }`}
            >
              {isPositive ? "+" : ""}
              {dailyPct.toFixed(2)}% today
            </div>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-[var(--border-subtle)]">
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">
            Total P&L
          </div>
          <div
            className={`text-sm font-mono tabular-nums ${
              totalPnl >= 0
                ? "text-[var(--accent-green)]"
                : "text-[var(--accent-red)]"
            }`}
          >
            {totalPnl >= 0 ? "+" : ""}
            {formatUSD(totalPnl)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

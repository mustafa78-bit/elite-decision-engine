import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatUSD } from "../../lib/utils";

interface DrawdownWidgetProps {
  currentDrawdown?: number;
  maxDrawdown?: number;
  peakValue?: number;
  currentValue?: number;
}

export function DrawdownWidget({
  currentDrawdown = 0,
  maxDrawdown = 0,
  peakValue = 0,
}: DrawdownWidgetProps) {
  const ddPct = peakValue > 0 ? (currentDrawdown / peakValue) * 100 : 0;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Drawdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="28" fill="none" stroke="var(--bg-elevated)" strokeWidth="4" />
              <circle
                cx="32" cy="32" r="28" fill="none" stroke="var(--accent-red)" strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={`${Math.min(ddPct / 100, 1) * 176} 176`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-mono font-bold tabular-nums text-[var(--accent-red)]">
                {ddPct.toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <div>
              <div className="text-[12px] text-[var(--text-muted)]">Current</div>
              <div className="text-sm font-mono tabular-nums text-[var(--accent-red)]">
                {formatUSD(Math.abs(currentDrawdown))}
              </div>
            </div>
            <div>
              <div className="text-[12px] text-[var(--text-muted)]">Max</div>
              <div className="text-sm font-mono tabular-nums text-[var(--accent-red)]">
                {Math.abs(maxDrawdown).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

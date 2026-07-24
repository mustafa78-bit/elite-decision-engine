import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatUSD } from "../../lib/utils";

interface VaRCardWidgetProps {
  var95?: number;
  var99?: number;
  volatility?: number;
  beta?: number;
  correlation?: number;
}

export function VaRCardWidget({
  var95 = 0,
  var99 = 0,
  volatility = 0,
  beta = 0,
}: VaRCardWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Value at Risk</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        <div className="p-2 rounded-lg bg-[var(--bg-elevated)]/50">
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">VaR 95%</div>
          <div className="text-sm font-mono tabular-nums text-[var(--accent-red)]">
            {formatUSD(Math.abs(var95))}
          </div>
        </div>
        <div className="p-2 rounded-lg bg-[var(--bg-elevated)]/50">
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">VaR 99%</div>
          <div className="text-sm font-mono tabular-nums text-[var(--accent-red)]">
            {formatUSD(Math.abs(var99))}
          </div>
        </div>
        <div className="p-2 rounded-lg bg-[var(--bg-elevated)]/50">
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Volatility</div>
          <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
            {(volatility * 100).toFixed(1)}%
          </div>
        </div>
        <div className="p-2 rounded-lg bg-[var(--bg-elevated)]/50">
          <div className="text-[12px] text-[var(--text-muted)] uppercase tracking-wider">Beta</div>
          <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
            {beta.toFixed(2)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

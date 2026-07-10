import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatUSD } from "../../lib/utils";

interface ExposureWidgetProps {
  longExposure?: number;
  shortExposure?: number;
  totalExposure?: number;
  buyingPower?: number;
}

export function ExposureWidget({
  longExposure = 0,
  shortExposure = 0,
  totalExposure = 0,
  buyingPower = 0,
}: ExposureWidgetProps) {
  const usagePct = buyingPower > 0 ? (totalExposure / buyingPower) * 100 : 0;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Exposure</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <div className="p-2 rounded-lg bg-[var(--accent-green)]/5 border border-[var(--accent-green)]/10">
            <div className="text-[10px] text-[var(--text-muted)]">Long</div>
            <div className="text-sm font-mono tabular-nums text-[var(--accent-green)]">
              {formatUSD(longExposure)}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-[var(--accent-red)]/5 border border-[var(--accent-red)]/10">
            <div className="text-[10px] text-[var(--text-muted)]">Short</div>
            <div className="text-sm font-mono tabular-nums text-[var(--accent-red)]">
              {formatUSD(shortExposure)}
            </div>
          </div>
        </div>
        <div>
          <div className="flex justify-between text-[10px] text-[var(--text-muted)] mb-1">
            <span>Usage</span>
            <span className="font-mono">{usagePct.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[var(--accent-green)] to-[var(--accent-yellow)] transition-all"
              style={{ width: `${Math.min(usagePct, 100)}%` }}
            />
          </div>
        </div>
        <div className="flex justify-between text-[10px]">
          <span className="text-[var(--text-muted)]">Buying Power</span>
          <span className="font-mono text-[var(--text-secondary)]">
            {formatUSD(buyingPower)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

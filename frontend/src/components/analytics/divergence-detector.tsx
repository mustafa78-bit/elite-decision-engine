import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface Divergence {
  symbol: string;
  type: "regular" | "hidden";
  direction: "bullish" | "bearish";
  indicator: string;
  strength: number;
  description: string;
}

interface DivergenceDetectorProps {
  divergences?: Divergence[];
}

export function DivergenceDetector({
  divergences = [
    { symbol: "BTC/USDT", type: "regular", direction: "bullish", indicator: "RSI", strength: 78, description: "Price made lower low, RSI made higher low — potential reversal up" },
    { symbol: "ETH/USDT", type: "hidden", direction: "bearish", indicator: "MACD", strength: 65, description: "Price made higher high, MACD made lower high — trend weakening" },
  ],
}: DivergenceDetectorProps) {
  if (divergences.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Divergence Detector</CardTitle></CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No divergences detected</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Divergence Detector</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {divergences.map((d) => (
          <div key={`${d.symbol}-${d.indicator}-${d.direction}`} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`text-[12px] ${d.direction === "bullish" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {d.direction === "bullish" ? "▲" : "▼"}
                </span>
                <span className="text-[12px] font-mono text-[var(--text-secondary)]">{d.symbol}</span>
                <Badge variant={d.direction === "bullish" ? "success" : "danger"} className="text-[11px]">{d.direction}</Badge>
                <Badge variant="info" className="text-[11px]">{d.type}</Badge>
              </div>
              <span className="text-[12px] font-mono text-[var(--text-muted)]">{d.indicator} · {d.strength}%</span>
            </div>
            <div className="text-[12px] text-[var(--text-muted)]">{d.description}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

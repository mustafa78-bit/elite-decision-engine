import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput } from "../ui/form";
import { Badge } from "../ui/badge";

interface ScenarioAnalyzerProps {
  symbol?: string;
}

export function ScenarioAnalyzer({ symbol = "BTC/USDT" }: ScenarioAnalyzerProps) {
  const [currentPrice, setCurrentPrice] = useState("42890");
  const [scenarioDown, setScenarioDown] = useState("-10");
  const [scenarioUp, setScenarioUp] = useState("+15");
  const [positionSize, setPositionSize] = useState("1.0");

  const scenarios = useMemo(() => {
    const price = parseFloat(currentPrice) || 0;
    const downPct = parseFloat(scenarioDown) || 0;
    const upPct = parseFloat(scenarioUp) || 0;
    const size = parseFloat(positionSize) || 0;

    return [
      { name: "Bear Case", change: downPct, price: price * (1 + downPct / 100), pnl: price * size * (downPct / 100) },
      { name: "Base Case", change: 0, price: price, pnl: 0 },
      { name: "Bull Case", change: upPct, price: price * (1 + upPct / 100), pnl: price * size * (upPct / 100) },
    ];
  }, [currentPrice, scenarioDown, scenarioUp, positionSize]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Scenario Analyzer</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Current Price</label>
            <FormInput value={currentPrice} onChange={(e) => setCurrentPrice(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Position Size</label>
            <FormInput value={positionSize} onChange={(e) => setPositionSize(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Bear Case (%)</label>
            <FormInput value={scenarioDown} onChange={(e) => setScenarioDown(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Bull Case (%)</label>
            <FormInput value={scenarioUp} onChange={(e) => setScenarioUp(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        {scenarios.map((s) => (
          <div
            key={s.name}
            className={`p-2 rounded-lg border text-[10px] font-mono ${
              s.change === 0
                ? "bg-[var(--bg-base)] border-[var(--border-subtle)]"
                : s.change > 0
                  ? "bg-green-950/30 border-green-800/30"
                  : "bg-red-950/30 border-red-800/30"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-secondary)]">{s.name}</span>
              <div className="flex items-center gap-2">
                <Badge variant={s.change > 0 ? "success" : s.change < 0 ? "danger" : "default"} className="text-[8px]">
                  {s.change > 0 ? "+" : ""}{s.change}%
                </Badge>
                <span className="tabular-nums text-[var(--text-primary)]">${s.price.toFixed(1)}</span>
                <span className={`tabular-nums ${s.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {s.pnl >= 0 ? "+" : ""}${s.pnl.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

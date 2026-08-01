import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput, FormSelect } from "../ui/form";
import { Badge } from "../ui/badge";

interface SmartStopLossProps {
  symbol?: string;
}

export function SmartStopLoss({ symbol = "BTC/USDT" }: SmartStopLossProps) {
  const [entryPrice, setEntryPrice] = useState("42890");
  const [currentPrice, setCurrentPrice] = useState("43850");
  const [positionSide, setPositionSide] = useState("long");
  const [volatility, setVolatility] = useState("2.4");

  const recommendations = useMemo(() => {
    const entry = parseFloat(entryPrice) || 0;
    const current = parseFloat(currentPrice) || 0;
    const vol = parseFloat(volatility) || 0;
    const isLong = positionSide === "long";

    return [
      { name: "Fixed %", stop: isLong ? entry * (1 - 0.02) : entry * (1 + 0.02), distance: "2.0%", risk: "Low" },
      { name: "ATR (1.5x)", stop: isLong ? current - vol * 1.5 : current + vol * 1.5, distance: `${(vol * 1.5 / current * 100).toFixed(1)}%`, risk: "Medium" },
      { name: "ATR (2.5x)", stop: isLong ? current - vol * 2.5 : current + vol * 2.5, distance: `${(vol * 2.5 / current * 100).toFixed(1)}%`, risk: "Low" },
      { name: "Support Level", stop: isLong ? entry * (1 - 0.035) : entry * (1 + 0.035), distance: "3.5%", risk: "Low" },
      { name: "Trailing", stop: isLong ? current * (1 - 0.015) : current * (1 + 0.015), distance: "1.5%", risk: "Medium" },
    ];
  }, [entryPrice, currentPrice, positionSide, volatility]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Smart Stop-Loss</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Entry</label>
            <FormInput value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Current</label>
            <FormInput value={currentPrice} onChange={(e) => setCurrentPrice(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Side</label>
            <FormSelect value={positionSide} onChange={(e) => setPositionSide(e.target.value)} className="h-7 text-[10px]">
              <option value="long">Long</option>
              <option value="short">Short</option>
            </FormSelect>
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">ATR ($)</label>
            <FormInput value={volatility} onChange={(e) => setVolatility(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        {recommendations.map((r) => (
          <div key={r.name} className="flex items-center justify-between px-2 py-1 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[10px] font-mono">
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-secondary)]">{r.name}</span>
              <span className={`text-[9px] ${r.risk === "Low" ? "text-[var(--accent-green)]" : "text-[var(--accent-yellow)]"}`}>{r.risk}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="tabular-nums">${r.stop.toFixed(1)}</span>
              <Badge variant="default" className="text-[8px]">{r.distance}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

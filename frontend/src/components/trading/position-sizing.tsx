import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput } from "../ui/form";

interface PositionSizingProps {
  symbol?: string;
  price?: number;
}

export function PositionSizing({ symbol = "BTC/USDT", price = 42890 }: PositionSizingProps) {
  const [accountSize, setAccountSize] = useState("50000");
  const [riskPercent, setRiskPercent] = useState("2");
  const [stopLossPct, setStopLossPct] = useState("5");
  const [leverage, setLeverage] = useState("1");

  const result = useMemo(() => {
    const account = parseFloat(accountSize) || 0;
    const risk = parseFloat(riskPercent) || 0;
    const sl = parseFloat(stopLossPct) || 0;
    const lev = parseFloat(leverage) || 1;

    const riskAmount = account * (risk / 100);
    const positionSize = sl > 0 ? (riskAmount / (sl / 100)) * lev : 0;
    const units = price > 0 ? positionSize / price : 0;
    const marginRequired = positionSize / lev;

    return { riskAmount, positionSize, units, marginRequired };
  }, [accountSize, riskPercent, stopLossPct, leverage, price]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Position Sizing</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol} @ ${price.toLocaleString()}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Account Size</label>
            <FormInput value={accountSize} onChange={(e) => setAccountSize(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Risk %</label>
            <FormInput value={riskPercent} onChange={(e) => setRiskPercent(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Stop Loss %</label>
            <FormInput value={stopLossPct} onChange={(e) => setStopLossPct(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Leverage</label>
            <FormInput value={leverage} onChange={(e) => setLeverage(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        <div className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-1">
          <div className="flex justify-between text-[10px] font-mono">
            <span className="text-[var(--text-muted)]">Risk Amount</span>
            <span className="text-[var(--accent-red)] tabular-nums">${result.riskAmount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-[10px] font-mono">
            <span className="text-[var(--text-muted)]">Position Size</span>
            <span className="text-[var(--text-primary)] tabular-nums">${result.positionSize.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-[10px] font-mono">
            <span className="text-[var(--text-muted)]">Units</span>
            <span className="text-[var(--accent-blue)] tabular-nums">{result.units.toFixed(4)} {symbol.split("/")[0]}</span>
          </div>
          <div className="flex justify-between text-[10px] font-mono">
            <span className="text-[var(--text-muted)]">Margin Required</span>
            <span className="text-[var(--text-secondary)] tabular-nums">${result.marginRequired.toFixed(2)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput } from "../ui/form";
import { Badge } from "../ui/badge";

interface ProfitTargetOptimizerProps {
  symbol?: string;
}

export function ProfitTargetOptimizer({ symbol = "BTC/USDT" }: ProfitTargetOptimizerProps) {
  const [entryPrice, setEntryPrice] = useState("42890");
  const [riskAmount, setRiskAmount] = useState("500");
  const [riskReward, setRiskReward] = useState("3");

  const targets = useMemo(() => {
    const entry = parseFloat(entryPrice) || 0;
    const risk = parseFloat(riskAmount) || 0;
    const rr = parseFloat(riskReward) || 0;
    const stopDistance = risk / entry;

    return [
      { level: "TP 1", multiplier: 1, price: entry + stopDistance * 1 * rr / 3, pnl: risk * rr / 3, prob: "High" },
      { level: "TP 2", multiplier: 2, price: entry + stopDistance * rr / 3 * 2, pnl: risk * rr / 3 * 2, prob: "Medium" },
      { level: "TP 3", multiplier: 3, price: entry + stopDistance * rr, pnl: risk * rr, prob: "Low" },
    ];
  }, [entryPrice, riskAmount, riskReward]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Profit Target Optimizer</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Entry Price</label>
            <FormInput value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Risk Amount ($)</label>
            <FormInput value={riskAmount} onChange={(e) => setRiskAmount(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-[9px] font-mono text-[var(--text-muted)]">Target R:R</label>
          <FormInput value={riskReward} onChange={(e) => setRiskReward(e.target.value)} className="h-7 text-[10px]" />
        </div>
        <div className="space-y-1.5 pt-1">
          {targets.map((t) => (
            <div key={t.level} className="flex items-center justify-between px-2 py-1 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[10px] font-mono">
              <div className="flex items-center gap-2">
                <span className="text-[var(--text-secondary)]">{t.level}</span>
                <Badge variant={t.prob === "High" ? "success" : t.prob === "Medium" ? "warning" : "default"} className="text-[8px]">{t.prob}</Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="tabular-nums">${t.price.toFixed(1)}</span>
                <span className="tabular-nums text-[var(--accent-green)]">+${t.pnl.toFixed(0)}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

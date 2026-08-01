import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput } from "../ui/form";
import { Badge } from "../ui/badge";

interface RiskRewardProps {
  symbol?: string;
}

export function RiskReward({ symbol = "BTC/USDT" }: RiskRewardProps) {
  const [entry, setEntry] = useState("42890");
  const [stopLoss, setStopLoss] = useState("41500");
  const [takeProfit, setTakeProfit] = useState("45000");

  const result = useMemo(() => {
    const e = parseFloat(entry) || 0;
    const sl = parseFloat(stopLoss) || 0;
    const tp = parseFloat(takeProfit) || 0;

    const riskAmt = e - sl;
    const rewardAmt = tp - e;
    const rrRatio = riskAmt > 0 ? (rewardAmt / riskAmt) : 0;
    const riskPct = e > 0 ? (Math.abs(riskAmt) / e) * 100 : 0;
    const rewardPct = e > 0 ? (rewardAmt / e) * 100 : 0;
    const winRateNeeded = rrRatio > 0 ? 1 / (1 + rrRatio) : 0;

    return { riskAmt, rewardAmt, rrRatio, riskPct, rewardPct, winRateNeeded };
  }, [entry, stopLoss, takeProfit]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Risk / Reward</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-3 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Entry</label>
            <FormInput value={entry} onChange={(e) => setEntry(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Stop Loss</label>
            <FormInput value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Take Profit</label>
            <FormInput value={takeProfit} onChange={(e) => setTakeProfit(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>

        <div className="relative h-8 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] overflow-hidden">
          <div
            className="absolute top-0 bottom-0 bg-[var(--accent-red)]/20"
            style={{
              left: 0,
              width: `${Math.min(result.rrRatio > 0 ? 100 / (1 + result.rrRatio) : 50, 80)}%`,
            }}
          />
          <div
            className="absolute top-0 bottom-0 bg-[var(--accent-green)]/20"
            style={{
              right: 0,
              width: `${Math.min(result.rrRatio > 0 ? (result.rrRatio / (1 + result.rrRatio)) * 100 : 50, 80)}%`,
            }}
          />
          <div className="absolute inset-0 flex items-center justify-center text-[9px] font-mono text-[var(--text-muted)]">
            1 : {result.rrRatio.toFixed(2)}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="p-2 rounded-lg bg-red-950/30 border border-red-800/30">
            <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase">Risk</div>
            <div className="text-[11px] font-mono text-[var(--accent-red)] tabular-nums">
              ${Math.abs(result.riskAmt).toFixed(1)} ({result.riskPct.toFixed(2)}%)
            </div>
          </div>
          <div className="p-2 rounded-lg bg-green-950/30 border border-green-800/30">
            <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase">Reward</div>
            <div className="text-[11px] font-mono text-[var(--accent-green)] tabular-nums">
              ${result.rewardAmt.toFixed(1)} ({result.rewardPct.toFixed(2)}%)
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[9px] font-mono text-[var(--text-muted)]">Min Win Rate Needed</span>
          <Badge variant={result.winRateNeeded <= 0.5 ? "success" : result.winRateNeeded <= 0.6 ? "warning" : "danger"}>
            {(result.winRateNeeded * 100).toFixed(1)}%
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

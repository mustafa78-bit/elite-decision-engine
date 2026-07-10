import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput } from "../ui/form";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";

export function OCOPanel() {
  const [side, setSide] = useState<"BUY" | "SELL">("SELL");
  const [entryPrice, setEntryPrice] = useState("42890");
  const [tpPrice, setTpPrice] = useState("43500");
  const [slPrice, setSlPrice] = useState("42000");
  const [amount, setAmount] = useState("0.1");

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>OCO Order</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">One-Cancels-Other</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex rounded-lg overflow-hidden border border-[var(--border-default)]">
          {(["BUY", "SELL"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSide(s)}
              className={cn(
                "flex-1 py-1.5 text-xs font-mono font-medium transition-all",
                side === s
                  ? s === "BUY" ? "bg-[var(--accent-green)] text-white" : "bg-[var(--accent-red)] text-white"
                  : "bg-[var(--bg-base)] text-[var(--text-muted)]",
              )}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Entry Price</label>
            <FormInput value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Amount</label>
            <FormInput value={amount} onChange={(e) => setAmount(e.target.value)} className="h-7 text-[10px]" />
          </div>
        </div>
        <div className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--accent-green)]" />
              <span className="text-[10px] font-mono text-[var(--text-secondary)]">Take Profit</span>
            </div>
            <FormInput value={tpPrice} onChange={(e) => setTpPrice(e.target.value)} className="h-6 w-24 text-[10px]" />
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--accent-red)]" />
              <span className="text-[10px] font-mono text-[var(--text-secondary)]">Stop Loss</span>
            </div>
            <FormInput value={slPrice} onChange={(e) => setSlPrice(e.target.value)} className="h-6 w-24 text-[10px]" />
          </div>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono">
          <span className="text-[var(--text-muted)]">Potential R:R</span>
          <Badge variant="info">
            1:{((parseFloat(tpPrice || "0") - parseFloat(entryPrice || "0")) / (parseFloat(entryPrice || "0") - parseFloat(slPrice || "0"))).toFixed(2)}
          </Badge>
        </div>
        <Button variant="primary" className="w-full h-8 text-xs">Place OCO Order</Button>
      </CardContent>
    </Card>
  );
}

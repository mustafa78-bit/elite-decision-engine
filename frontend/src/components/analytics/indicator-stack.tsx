import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { cn } from "../../lib/utils";

interface IndicatorValue {
  name: string;
  value: string;
  signal: "buy" | "sell" | "neutral";
  category: string;
}

interface IndicatorStackProps {
  indicators?: IndicatorValue[];
}

export function IndicatorStack({
  indicators = [
    { name: "RSI (14)", value: "58.2", signal: "neutral", category: "Momentum" },
    { name: "MACD", value: "Bullish", signal: "buy", category: "Momentum" },
    { name: "Stoch RSI", value: "62.5", signal: "neutral", category: "Momentum" },
    { name: "EMA (20)", value: "$42,150", signal: "buy", category: "Trend" },
    { name: "EMA (50)", value: "$41,800", signal: "buy", category: "Trend" },
    { name: "EMA (200)", value: "$40,200", signal: "buy", category: "Trend" },
    { name: "Bollinger Width", value: "2.8%", signal: "neutral", category: "Volatility" },
    { name: "ATR (14)", value: "$520", signal: "neutral", category: "Volatility" },
    { name: "OBV", value: "Rising", signal: "buy", category: "Volume" },
    { name: "Volume", value: "1.8x avg", signal: "buy", category: "Volume" },
  ],
}: IndicatorStackProps) {
  const [categoryFilter, setCategoryFilter] = useState("all");
  const categories = Array.from(new Set(indicators.map((i) => i.category)));

  const filtered = categoryFilter === "all" ? indicators : indicators.filter((i) => i.category === categoryFilter);

  const buys = indicators.filter((i) => i.signal === "buy").length;
  const sells = indicators.filter((i) => i.signal === "sell").length;

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            Indicators
            <span className="text-[12px] font-mono text-[var(--text-muted)] ml-2">{buys}B / {sells}S</span>
          </CardTitle>
          <div className="flex gap-1">
            <button onClick={() => setCategoryFilter("all")} className={cn("px-1.5 py-0.5 rounded text-[11px] font-mono transition-all", categoryFilter === "all" ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]" : "text-[var(--text-muted)]")}>
              All
            </button>
            {categories.map((c) => (
              <button key={c} onClick={() => setCategoryFilter(c)} className={cn("px-1.5 py-0.5 rounded text-[11px] font-mono transition-all", categoryFilter === c ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]" : "text-[var(--text-muted)]")}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-0.5">
        {filtered.map((ind) => (
          <div key={ind.name} className="flex items-center justify-between px-2 py-1 rounded-lg text-[12px] font-mono hover:bg-[var(--bg-hover)]">
            <span className="text-[var(--text-secondary)]">{ind.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-primary)] tabular-nums">{ind.value}</span>
              <span className={cn(
                "text-[12px] font-mono",
                ind.signal === "buy" ? "text-[var(--accent-green)]" : ind.signal === "sell" ? "text-[var(--accent-red)]" : "text-[var(--text-muted)]",
              )}>
                {ind.signal === "buy" ? "▲" : ind.signal === "sell" ? "▼" : "—"}
              </span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

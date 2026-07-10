import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

const CONDITION_LABELS: Record<string, string> = {
  rsi_oversold: "RSI < 30",
  rsi_overbought: "RSI > 70",
  ema_cross_above: "EMA 9 × EMA 21 Cross Above",
  volume_spike: "Volume > 2x Avg",
  macd_bullish: "MACD Bullish Cross",
  above_vwap: "Price > VWAP",
};

const ACTION_LABELS: Record<string, string> = {
  buy_market: "Buy Market",
  sell_market: "Sell Market",
  buy_limit: "Buy Limit",
  sell_limit: "Sell Limit",
  set_stop: "Set Stop-Loss",
  set_tp: "Set Take-Profit",
  cancel_orders: "Cancel All Orders",
};

interface StrategyBuilderProps {
  onSave?: (name: string) => void;
}

export function StrategyBuilder({ onSave }: StrategyBuilderProps) {
  const [strategyName, setStrategyName] = useState("My Strategy");
  const [conditions, setConditions] = useState<string[]>(["rsi_oversold", "ema_cross_above"]);
  const [actions, setActions] = useState<string[]>(["buy_market", "set_stop"]);

  const toggleCondition = (c: string) => {
    setConditions((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  };

  const toggleAction = (a: string) => {
    setActions((prev) =>
      prev.includes(a) ? prev.filter((x) => x !== a) : [...prev, a]
    );
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Strategy Builder</CardTitle>
          <Badge variant="info">{conditions.length} conds · {actions.length} acts</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2">
          <input
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            className="flex-1 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded px-2 h-7 text-[10px] font-mono text-[var(--text-primary)]"
          />
          <Button variant="primary" className="h-7 text-[10px]" onClick={() => onSave?.(strategyName)}>Save</Button>
        </div>
        <div>
          <div className="text-[9px] font-mono text-[var(--text-muted)] mb-1 uppercase">Conditions (All Must Match)</div>
          <div className="flex flex-wrap gap-1">
            {Object.entries(CONDITION_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => toggleCondition(key)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono border transition-colors ${
                  conditions.includes(key)
                    ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[9px] font-mono text-[var(--text-muted)] mb-1 uppercase">Actions (Executed In Order)</div>
          <div className="flex flex-wrap gap-1">
            {Object.entries(ACTION_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => toggleAction(key)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono border transition-colors ${
                  actions.includes(key)
                    ? "bg-[var(--accent-green)]/20 border-[var(--accent-green)] text-[var(--accent-green)]"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

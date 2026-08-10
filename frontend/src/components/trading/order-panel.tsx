import { useState } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormInput } from "../ui/form";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";
import { useTerminalStore } from "../../stores/terminal-store";

type OrderSide = "BUY" | "SELL";
type OrderType = "MARKET" | "LIMIT" | "STOP";

export function OrderPanel() {
  const { t } = useTranslation("tradingWorkspace");
  const sideLabels: Record<OrderSide, string> = {
    BUY: t("orderPanel.side.buy"),
    SELL: t("orderPanel.side.sell"),
  };
  const typeLabels: Record<OrderType, string> = {
    MARKET: t("orderPanel.type.market"),
    LIMIT: t("orderPanel.type.limit"),
    STOP: t("orderPanel.type.stop"),
  };
  const { symbol: rawSymbol } = useTerminalStore();
  const symbol = rawSymbol ?? "BTCUSDT";
  const [side, setSide] = useState<OrderSide>("BUY");
  const [orderType, setOrderType] = useState<OrderType>("LIMIT");
  const [price, setPrice] = useState("42890.00");
  const [amount, setAmount] = useState("0.1");
  const [reduceOnly, setReduceOnly] = useState(false);

  const total = parseFloat(price || "0") * parseFloat(amount || "0");

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{t("orderPanel.title")}</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {symbol}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex rounded-lg overflow-hidden border border-[var(--border-default)]">
          {(["BUY", "SELL"] as OrderSide[]).map((s) => (
            <button
              key={s}
              onClick={() => setSide(s)}
              className={cn(
                "flex-1 py-1.5 text-xs font-mono font-medium transition-all",
                side === s
                  ? s === "BUY"
                    ? "bg-[var(--accent-green)] text-white"
                    : "bg-[var(--accent-red)] text-white"
                  : "bg-[var(--bg-base)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
              )}
            >
              {sideLabels[s]}
            </button>
          ))}
        </div>

        <div className="flex gap-1 rounded-lg overflow-hidden border border-[var(--border-default)] p-0.5 bg-[var(--bg-base)]">
          {(["MARKET", "LIMIT", "STOP"] as OrderType[]).map((ot) => (
            <button
              key={ot}
              onClick={() => setOrderType(ot)}
              className={cn(
                "flex-1 py-1 text-[10px] font-mono rounded-md transition-all",
                orderType === ot
                  ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
              )}
            >
              {typeLabels[ot]}
            </button>
          ))}
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
            {t("orderPanel.price")}
          </label>
          <FormInput
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="h-8 text-xs"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
            {t("orderPanel.amount", { symbol: symbol.split("/")[0] })}
          </label>
          <FormInput
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="h-8 text-xs"
          />
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono text-[var(--text-secondary)]">
          <span>{t("orderPanel.total")}</span>
          <span className="tabular-nums">
            {total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT
          </span>
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={reduceOnly}
            onChange={(e) => setReduceOnly(e.target.checked)}
            className="rounded border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]/30"
          />
          <span className="text-[10px] text-[var(--text-muted)]">{t("orderPanel.reduceOnly")}</span>
        </label>

        <motion.div whileTap={{ scale: 0.98 }}>
          <Button
            variant={side === "BUY" ? "primary" : "danger"}
            className="w-full h-9 text-xs font-mono"
          >
            {sideLabels[side]} {symbol.split("/")[0]}
          </Button>
        </motion.div>
      </CardContent>
    </Card>
  );
}

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";

interface Order {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  type: "MARKET" | "LIMIT" | "STOP" | "OCO" | "TRAILING_STOP";
  price: number;
  amount: number;
  filled: number;
  status: "filled" | "partial" | "pending" | "cancelled" | "rejected";
  time: string;
}

interface OrderHistoryProps {
  orders?: Order[];
}

const statusColors: Record<string, "success" | "warning" | "info" | "danger" | "default"> = {
  filled: "success",
  partial: "warning",
  pending: "info",
  cancelled: "default",
  rejected: "danger",
};

export function OrderHistory({ orders = [] }: OrderHistoryProps) {
  const [filter, setFilter] = useState<string>("all");

  const filters = ["all", "filled", "pending", "cancelled"];
  const filtered = filter === "all" ? orders : orders.filter((o) => o.status === filter);

  if (orders.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Order History</CardTitle></CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No orders yet</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Order History</CardTitle>
          <div className="flex gap-1">
            {filters.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-1.5 py-0.5 rounded text-[11px] font-mono uppercase transition-all",
                  filter === f
                    ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-3 py-1 border-b border-[var(--border-subtle)] flex text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          <span className="flex-[2]">Symbol</span>
          <span className="flex-[1]">Type</span>
          <span className="flex-[1] text-right">Price</span>
          <span className="flex-[1] text-right">Filled</span>
          <span className="flex-[1] text-right">Status</span>
        </div>
        {filtered.map((o) => (
          <div key={o.id} className="flex items-center px-3 py-1.5 text-[12px] font-mono border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
            <div className="flex-[2] flex items-center gap-1.5">
              <span className={o.side === "BUY" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                {o.side === "BUY" ? "▲" : "▼"}
              </span>
              <span className="text-[var(--text-secondary)]">{o.symbol}</span>
            </div>
            <span className="flex-[1] text-[var(--text-muted)]">{o.type}</span>
            <span className="flex-[1] text-right text-[var(--text-primary)] tabular-nums">${o.price.toFixed(1)}</span>
            <span className="flex-[1] text-right text-[var(--text-muted)] tabular-nums">{((o.filled / o.amount) * 100).toFixed(0)}%</span>
            <span className="flex-[1] text-right">
              <Badge variant={statusColors[o.status]} className="text-[11px]">{o.status}</Badge>
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { formatUSD } from "../../lib/utils";
import type { TradePayload } from "../../types/trade";

interface PositionsListWidgetProps {
  positions?: TradePayload[];
  loading?: boolean;
}

export function PositionsListWidget({ positions = [], loading = false }: PositionsListWidgetProps) {
  const navigate = useNavigate();

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/trades")}
      role="region"
      aria-label="Active Positions"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/trades");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Open Positions</span>
              <span className="text-[8px] bg-[var(--accent-green)]/15 text-[var(--accent-green)] px-1 rounded uppercase tracking-[0.05em] font-mono">
                {positions.length} ACTIVE
              </span>
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          {loading ? (
            <div className="space-y-1.5 py-4">
              <div className="h-4 bg-[var(--bg-elevated)] rounded animate-pulse" />
              <div className="h-4 bg-[var(--bg-elevated)] rounded animate-pulse" />
            </div>
          ) : positions.length === 0 ? (
            <div className="text-[10px] font-mono text-[var(--text-muted)] text-center py-6">
              No active open positions.
            </div>
          ) : (
            <div className="space-y-1 max-h-[160px] overflow-y-auto pr-0.5">
              <div className="grid grid-cols-5 gap-1 text-[8px] font-mono font-semibold text-[var(--text-muted)] uppercase tracking-wider px-1 pb-1">
                <span>Asset</span>
                <span>Side</span>
                <span className="text-right">Qty</span>
                <span className="text-right">Entry</span>
                <span className="text-right">PnL</span>
              </div>
              {positions.map((p, i) => {
                const isLong = p.side === "LONG";
                const pnl = p.pnl ?? 0;
                const isPositive = pnl >= 0;

                return (
                  <div key={p.trade_id || i}>
                    <div className="grid grid-cols-5 gap-1 items-center px-1 py-1.5 rounded hover:bg-[var(--bg-elevated)] transition-colors text-[10px]">
                      <span className="font-mono font-bold text-[var(--text-primary)]">
                        {p.symbol}
                      </span>
                      <div>
                        <Badge variant={isLong ? "success" : "danger"} className="text-[8px] px-1 py-0 uppercase">
                          {p.side}
                        </Badge>
                      </div>
                      <span className="font-mono tabular-nums text-right text-[var(--text-secondary)]">
                        {((p as any).size ?? 1.0).toLocaleString()}
                      </span>
                      <span className="font-mono tabular-nums text-right text-[var(--text-secondary)]">
                        {formatUSD(p.entry)}
                      </span>
                      <span
                        className={`font-mono tabular-nums text-right font-bold ${
                          isPositive ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                        }`}
                      >
                        {isPositive ? "+" : ""}
                        {formatUSD(pnl)}
                      </span>
                    </div>
                    {i < positions.length - 1 && <Separator className="my-0.5" />}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Brokerage: Hyperliquid Paper</span>
          <span className="text-[var(--text-primary)]">Margin Leveraged: 10x</span>
        </div>
      </CardContent>
    </Card>
  );
}

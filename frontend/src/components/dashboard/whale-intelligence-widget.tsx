import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";

interface WhaleTx {
  hash: string;
  symbol: string;
  amount: number;
  usdValue: number;
  from: string;
  to: string;
  timestamp: string;
  type: "INFLOW" | "OUTFLOW" | "TRANSFER";
}

const mockWhaleTxs: WhaleTx[] = [
  { hash: "0x3f5c...921", symbol: "BTC", amount: 450, usdValue: 43852500, from: "Binance Cold Wallet", to: "Unknown Whale", timestamp: "2m ago", type: "OUTFLOW" },
  { hash: "0xa12b...e4f", symbol: "ETH", amount: 12500, usdValue: 42750000, from: "Unknown Whale", to: "Coinbase Deposit", timestamp: "7m ago", type: "INFLOW" },
  { hash: "0x7d8a...1c2", symbol: "SOL", amount: 84000, usdValue: 14280000, from: "Kraken Outflow", to: "Self Custody", timestamp: "12m ago", type: "OUTFLOW" },
  { hash: "0xfe3c...29a", symbol: "USDT", amount: 25000000, usdValue: 25000000, from: "Tether Treasury", to: "Binance", timestamp: "18m ago", type: "INFLOW" },
  { hash: "0x882a...bf3", symbol: "LINK", amount: 350000, usdValue: 6125000, from: "Smart Money Wallet", to: "Uniswap LP", timestamp: "25m ago", type: "TRANSFER" },
];

export function WhaleIntelligenceWidget() {
  const navigate = useNavigate();

  const { data: txs, isLoading, error, refetch } = useQuery<WhaleTx[]>({
    queryKey: ["whale-intelligence-txs"],
    queryFn: async () => {
      // simulate network request
      await new Promise((resolve) => setTimeout(resolve, 300));
      return mockWhaleTxs;
    },
    refetchInterval: 12_000,
  });

  if (isLoading) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer">
        <div className="p-2.5">
          <Skeleton className="h-4 w-1/3 mb-2" />
          <Skeleton className="h-24 w-full" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all">
        <div className="p-3 flex flex-col items-center justify-center gap-2 h-full min-h-[140px]">
          <span className="text-[10px] font-mono text-[var(--accent-red)]">Whale Intelligence Failed</span>
          <button
            onClick={() => refetch()}
            className="px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] text-[9px] font-mono"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/whale")}
      role="region"
      aria-label="Whale Intelligence"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/whale");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Whale Intelligence</span>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          <div className="space-y-1 max-h-[160px] overflow-y-auto pr-0.5">
            {txs && txs.length > 0 ? (
              txs.map((tx) => (
                <div key={tx.hash} className="flex items-center justify-between py-1 border-b border-[var(--border-subtle)] last:border-0 hover:bg-[var(--bg-hover)] px-1 rounded transition-colors text-[10px]">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      tx.type === "INFLOW" ? "bg-[var(--accent-green)]" : tx.type === "OUTFLOW" ? "bg-[var(--accent-red)]" : "bg-[var(--accent-purple)]"
                    }`} />
                    <span className="font-mono font-bold text-[var(--text-primary)]">{tx.symbol}</span>
                    <span className="text-[var(--text-muted)]">{tx.amount >= 1000 ? `${(tx.amount/1000).toFixed(1)}K` : tx.amount.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[var(--text-secondary)] tabular-nums">
                      ${tx.usdValue >= 1_000_000 ? `${(tx.usdValue / 1_000_000).toFixed(1)}M` : tx.usdValue.toLocaleString()}
                    </span>
                    <Badge variant={tx.type === "INFLOW" ? "success" : tx.type === "OUTFLOW" ? "danger" : "info"} className="text-[8px] px-1 py-0 uppercase">
                      {tx.type}
                    </Badge>
                    <span className="text-[9px] text-[var(--text-muted)] font-mono tabular-nums whitespace-nowrap">{tx.timestamp}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-[10px] text-[var(--text-muted)] font-mono">
                No whale transactions detected
              </div>
            )}
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] flex items-center justify-between text-[9px] font-mono text-[var(--text-muted)]">
          <span>Active Smart Wallets: 184</span>
          <span className="text-[var(--accent-green)]">Aggregate Inflow: +$14.8M</span>
        </div>
      </CardContent>
    </Card>
  );
}

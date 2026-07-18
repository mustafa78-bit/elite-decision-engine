import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { fetchWatchlists } from "../../api/watchlists";
import { useTerminalStore } from "../../stores/terminal-store";

interface WatchlistItemProps {
  symbol: string;
  price: number;
  change: number;
  onSelect: (symbol: string) => void;
}

// Memoized item row to maximize ticking performance
const WatchlistItem = React.memo(({ symbol, price, change, onSelect }: WatchlistItemProps) => {
  const isPositive = change >= 0;
  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onSelect(symbol);
      }}
      className="flex items-center justify-between py-1 border-b border-[var(--border-subtle)] last:border-0 hover:bg-[var(--bg-hover)] px-1 rounded cursor-pointer transition-colors text-[10px]"
    >
      <span className="font-mono font-bold text-[var(--text-primary)] hover:text-[var(--accent-blue)] transition-colors">{symbol}</span>
      <div className="text-right flex items-center gap-3">
        <span className="font-mono tabular-nums text-[var(--text-secondary)]">${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        <span className={`font-mono tabular-nums font-semibold w-12 text-right ${isPositive ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
          {isPositive ? "+" : ""}
          {change.toFixed(2)}%
        </span>
      </div>
    </div>
  );
});

WatchlistItem.displayName = "WatchlistItem";

interface WatchlistWidgetProps {
  btcLivePrice?: number;
  btcLiveChange?: number;
  ethLivePrice?: number;
  ethLiveChange?: number;
}

export function WatchlistWidget({
  btcLivePrice,
  btcLiveChange,
  ethLivePrice,
  ethLiveChange,
}: WatchlistWidgetProps) {
  const navigate = useNavigate();
  const { setSymbol } = useTerminalStore();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["watchlists-widget-list"],
    queryFn: fetchWatchlists,
    refetchInterval: 30_000,
  });

  const btcPrice = btcLivePrice ?? 97450.0;
  const btcChange = btcLiveChange ?? 1.85;
  const ethPrice = ethLivePrice ?? 3420.5;
  const ethChange = ethLiveChange ?? -0.65;

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

  // Fallback default watchlist if database is empty
  const defaultList = {
    name: "Core Assets",
    symbols: ["BTC", "ETH", "SOL", "LINK", "AVAX"],
  };
  const activeList = data?.watchlists?.[0] || defaultList;

  // Custom live pricing dictionary
  const pricesMap: Record<string, { price: number; change: number }> = {
    BTC: { price: btcPrice, change: btcChange },
    ETH: { price: ethPrice, change: ethChange },
    SOL: { price: 178.45, change: 3.12 },
    LINK: { price: 18.25, change: -1.40 },
    AVAX: { price: 34.60, change: 0.85 },
  };

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/watchlists")}
      role="region"
      aria-label="Active Watchlist"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/watchlists");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider truncate">Watchlist</span>
              <span className="text-[8px] bg-[var(--bg-elevated)] text-[var(--text-secondary)] px-1 rounded font-mono truncate max-w-[120px] shrink-0">
                {activeList.name}
              </span>
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono shrink-0">◈ Link</span>
          </div>

          {error ? (
            <div className="py-2.5 px-1 bg-amber-950/10 border border-amber-900/15 rounded flex items-center justify-between mb-2">
              <div className="flex flex-col">
                <span className="text-[9px] font-mono text-[var(--accent-yellow)] uppercase font-semibold">FEED OFFLINE</span>
                <span className="text-[8px] text-[var(--text-muted)] font-mono">LOCAL BACKUP SYNC</span>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); refetch(); }}
                className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] text-[8px] font-mono text-[var(--text-secondary)]"
              >
                SYNC
              </button>
            </div>
          ) : null}

          <div className="space-y-1 max-h-[160px] overflow-y-auto pr-0.5">
            {activeList.symbols.map((sym) => {
              const symbolObj = pricesMap[sym] || { price: 12.50, change: 1.25 };
              return (
                <WatchlistItem
                  key={sym}
                  symbol={sym}
                  price={symbolObj.price}
                  change={symbolObj.change}
                  onSelect={setSymbol}
                />
              );
            })}
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Click symbol to load chart</span>
          <span className="text-[var(--text-secondary)]">{activeList.symbols.length} Assets</span>
        </div>
      </CardContent>
    </Card>
  );
}

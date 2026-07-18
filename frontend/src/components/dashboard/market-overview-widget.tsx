import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchRegime } from "../../api/regime";

interface LiveTickerProps {
  symbol: string;
  price: number;
  change: number;
}

// Memoized subcomponent to optimize rendering on fast real-time websocket price ticks
const LiveTicker = React.memo(({ symbol, price, change }: LiveTickerProps) => {
  const isPositive = change >= 0;
  return (
    <div className="flex items-center justify-between py-1 border-b border-[var(--border-subtle)] last:border-0 hover:bg-[var(--bg-hover)] px-1 rounded transition-colors">
      <span className="font-mono text-xs font-semibold text-[var(--text-primary)]">{symbol}</span>
      <div className="text-right">
        <div className="font-mono text-xs tabular-nums text-[var(--text-primary)]">
          ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className={`font-mono text-[10px] tabular-nums ${isPositive ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
          {isPositive ? "▲" : "▼"} {isPositive ? "+" : ""}{change.toFixed(2)}%
        </div>
      </div>
    </div>
  );
});

LiveTicker.displayName = "LiveTicker";

interface MarketOverviewWidgetProps {
  btcLivePrice?: number;
  btcLiveChange?: number;
  ethLivePrice?: number;
  ethLiveChange?: number;
}

export function MarketOverviewWidget({
  btcLivePrice,
  btcLiveChange,
  ethLivePrice,
  ethLiveChange,
}: MarketOverviewWidgetProps) {
  const navigate = useNavigate();

  const { data: regimeData, isLoading, error, refetch } = useQuery({
    queryKey: ["regime"],
    queryFn: fetchRegime,
    refetchInterval: 30_000,
  });

  const btcPrice = btcLivePrice ?? 97450.0;
  const btcChange = btcLiveChange ?? 1.85;
  const ethPrice = ethLivePrice ?? 3420.5;
  const ethChange = ethLiveChange ?? -0.65;

  const fearAndGreedText = useMemo(() => {
    const score = regimeData?.rsi ?? 65;
    if (score >= 75) return { label: "Extreme Greed", color: "var(--accent-green)" };
    if (score >= 55) return { label: "Greed", color: "var(--accent-cyan)" };
    if (score >= 45) return { label: "Neutral", color: "var(--accent-yellow)" };
    if (score >= 25) return { label: "Fear", color: "var(--accent-orange)" };
    return { label: "Extreme Fear", color: "var(--accent-red)" };
  }, [regimeData]);

  if (isLoading) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer">
        <div className="p-2.5">
          <Skeleton className="h-4 w-1/2 mb-2" />
          <Skeleton className="h-20 w-full" />
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/market")}
      role="region"
      aria-label="Global Market Overview"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/market");
        }
      }}
    >
      <CardContent className="p-2.5">
        <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider truncate">Market Overview</span>
            <span className="text-[8px] bg-[var(--accent-blue)]/15 text-[var(--accent-blue)] px-1 rounded uppercase tracking-[0.05em] font-mono shrink-0">LIVE</span>
          </div>
          <span className="text-[9px] text-[var(--text-muted)] font-mono shrink-0">◈ Link</span>
        </div>

        {error ? (
          <div className="py-2.5 px-1 bg-red-950/15 border border-red-900/20 rounded flex items-center justify-between mb-2">
            <div className="flex flex-col">
              <span className="text-[9px] font-mono text-[var(--accent-red)] uppercase font-semibold">FEED OFFLINE</span>
              <span className="text-[8px] text-[var(--text-muted)] font-mono">RECONNECTING FEED</span>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); refetch(); }}
              className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] text-[8px] font-mono text-[var(--text-secondary)]"
            >
              SYNC
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2 mb-2">
            <LiveTicker symbol="BTC/USDT" price={btcPrice} change={btcChange} />
            <LiveTicker symbol="ETH/USDT" price={ethPrice} change={ethChange} />
          </div>
        )}

        <div className="grid grid-cols-3 gap-1.5 pt-1.5 border-t border-[var(--border-subtle)]">
          <div className="text-left">
            <div className="text-[8px] uppercase text-[var(--text-muted)] font-mono font-semibold">Total Cap</div>
            <div className="text-[10px] font-bold font-mono text-[var(--text-primary)]">$2.45T</div>
            <div className="text-[8px] font-mono text-[var(--accent-green)]">+0.4%</div>
          </div>
          <div className="text-left">
            <div className="text-[8px] uppercase text-[var(--text-muted)] font-mono font-semibold">Dominance</div>
            <div className="text-[10px] font-bold font-mono text-[var(--text-primary)]">BTC 56.4%</div>
            <div className="text-[8px] font-mono text-[var(--text-secondary)]">ETH 17.2%</div>
          </div>
          <div className="text-left">
            <div className="text-[8px] uppercase text-[var(--text-muted)] font-mono font-semibold">Fear & Greed</div>
            <div className="text-[10px] font-bold font-mono" style={{ color: fearAndGreedText.color }}>
              {regimeData?.rsi ? Math.min(Math.max(Math.round(regimeData.rsi), 10), 90) : 68}
            </div>
            <div className="text-[8px] font-mono text-[var(--text-secondary)] leading-none truncate">
              {fearAndGreedText.label}
            </div>
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] flex items-center justify-between text-[10px]">
          <span className="text-[var(--text-muted)] font-mono text-[9px]">Regime State:</span>
          <Badge variant={regimeData?.trend === "BULLISH" ? "success" : "warning"} className="text-[8px] px-1 py-0 font-mono uppercase">
            {regimeData?.regime || "TREND"} ({regimeData?.trend || "BULLISH"})
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

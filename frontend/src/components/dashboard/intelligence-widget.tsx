import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";

interface IntelligenceItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  relevance?: number;
  sentiment?: "BULLISH" | "BEARISH" | "NEUTRAL";
}

const defaultNews: IntelligenceItem[] = [
  { id: "1", title: "SEC Formally Approves Spot Options Trading", summary: "Market liquidity expected to surge following approval of derivative options products for BTC.", source: "Reuters", timestamp: "12m ago", relevance: 94, sentiment: "BULLISH" },
  { id: "2", title: "Ethereum gas fees plunge to record lows", summary: "Layer-2 migration successfully moves over 80% of retail transactions away from mainnet.", source: "CoinDesk", timestamp: "35m ago", relevance: 88, sentiment: "NEUTRAL" },
  { id: "3", title: "US Dollar Index (DXY) climbs to 104.5", summary: "Strength in US macro indices places brief pressure on risk assets including crypto.", source: "Bloomberg", timestamp: "1h ago", relevance: 75, sentiment: "BEARISH" },
  { id: "4", title: "Whale transfers 12,500 ETH to Coinbase", summary: "On-chain monitoring registers large movement from self-custody cold wallets into exchanges.", source: "OnChain", timestamp: "2h ago", relevance: 82, sentiment: "BEARISH" },
];

interface IntelligenceWidgetProps {
  items?: IntelligenceItem[];
}

export function IntelligenceWidget({ items = defaultNews }: IntelligenceWidgetProps) {
  const navigate = useNavigate();

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/intelligence")}
      role="region"
      aria-label="Market Intelligence News Feed"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/intelligence");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Market Intelligence Feed</span>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-0.5">
            {items.map((item) => {
              const isBullish = item.sentiment === "BULLISH";
              const isBearish = item.sentiment === "BEARISH";
              return (
                <div
                  key={item.id}
                  className="p-1.5 rounded bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)] hover:border-[var(--border-default)] transition-all text-[10px]"
                >
                  <div className="flex items-start justify-between gap-1.5">
                    <div className="font-semibold text-[var(--text-primary)] leading-snug">
                      {item.title}
                    </div>
                    {item.relevance !== undefined && (
                      <Badge variant="info" className="shrink-0 text-[8px] px-0.5 py-0 scale-95 origin-right">
                        {item.relevance}% Rel
                      </Badge>
                    )}
                  </div>
                  <div className="text-[9px] text-[var(--text-secondary)] mt-0.5 line-clamp-2">
                    {item.summary}
                  </div>
                  <div className="flex items-center justify-between mt-1 pt-1 border-t border-[var(--border-subtle)] text-[8px] text-[var(--text-muted)]">
                    <div className="flex items-center gap-1.5">
                      <span>{item.source}</span>
                      <span className={`font-mono font-bold ${
                        isBullish ? "text-[var(--accent-green)]" : isBearish ? "text-[var(--accent-red)]" : "text-[var(--text-muted)]"
                      }`}>
                        {item.sentiment}
                      </span>
                    </div>
                    <span className="font-mono">{item.timestamp}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Sentiment Multi-Model Aggregate</span>
          <span className="text-[var(--accent-green)]">Bullish Score (68/100)</span>
        </div>
      </CardContent>
    </Card>
  );
}

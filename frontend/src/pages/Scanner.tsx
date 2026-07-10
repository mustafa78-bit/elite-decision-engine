import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Skeleton } from "../components/ui/skeleton";
import { apiFetch } from "../api/client";
import { useTerminalStore } from "../stores/terminal-store";
import { useNavigate } from "react-router-dom";

interface Opportunity {
  rank: number;
  symbol: string;
  side: string;
  strategy: string;
  score: number;
  probability: number;
  risk_score: number;
  confidence: number;
  price: number;
  signals: string[];
}

const CATEGORIES = [
  { id: "top-movers", label: "Top Movers" },
  { id: "top-breakouts", label: "Top Breakouts" },
  { id: "top-trends", label: "Top Trends" },
  { id: "top-reversals", label: "Top Reversals" },
  { id: "top-mean-reversions", label: "Mean Reversion" },
];

export default function Scanner() {
  const [activeCategory, setActiveCategory] = useState("top-movers");
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const { setSymbol, addRecentSymbol } = useTerminalStore();
  const navigate = useNavigate();

  const loadCategory = useCallback(async (category: string) => {
    setLoading(true);
    try {
      const data = await apiFetch<Opportunity[]>(`/scanner/category/${category}?n=20`);
      setOpportunities(data);
    } catch {
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategory(activeCategory);
  }, [activeCategory, loadCategory]);

  const filtered = search
    ? opportunities.filter((o) => o.symbol.toLowerCase().includes(search.toLowerCase()))
    : opportunities;

  const handleSelect = (symbol: string) => {
    setSymbol(symbol);
    addRecentSymbol(symbol);
    navigate(`/asset/${symbol}`);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
          Opportunity Scanner
        </h2>
        <Input
          placeholder="Search symbol..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-48 h-7 text-xs"
        />
      </div>

      <div className="flex gap-1 flex-wrap">
        {CATEGORIES.map((cat) => (
          <Button
            key={cat.id}
            variant={activeCategory === cat.id ? "primary" : "secondary"}
            size="sm"
            onClick={() => setActiveCategory(cat.id)}
          >
            {cat.label}
          </Button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-[var(--text-muted)] text-xs font-mono">
          No opportunities found for this category
        </div>
      ) : (
        <div className="space-y-1">
          {filtered.map((opp) => (
            <button
              key={`${opp.symbol}-${opp.rank}`}
              onClick={() => handleSelect(opp.symbol)}
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--border-default)] hover:bg-[var(--bg-hover)] transition-all text-left"
            >
              <span className="text-[10px] font-mono text-[var(--text-muted)] w-6">
                #{opp.rank}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[var(--text-primary)]">
                    {opp.symbol}
                  </span>
                  <Badge
                    variant={opp.side === "LONG" ? "success" : "danger"}
                    className="text-[9px]"
                  >
                    {opp.side}
                  </Badge>
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">
                    {opp.strategy}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="text-[10px] font-mono tabular-nums text-[var(--accent-blue)]">
                    Score: {opp.score.toFixed(2)}
                  </span>
                  <span className="text-[10px] font-mono tabular-nums text-[var(--accent-green)]">
                    Prob: {opp.probability.toFixed(0)}%
                  </span>
                  <span className="text-[10px] font-mono tabular-nums text-[var(--accent-yellow)]">
                    Conf: {opp.confidence.toFixed(0)}%
                  </span>
                  <span className="text-[10px] font-mono tabular-nums text-[var(--accent-red)]">
                    Risk: {opp.risk_score.toFixed(2)}
                  </span>
                </div>
              </div>
              {opp.signals.length > 0 && (
                <div className="hidden md:flex gap-1">
                  {opp.signals.slice(0, 3).map((s) => (
                    <Badge key={s} variant="default" className="text-[8px]">
                      {s}
                    </Badge>
                  ))}
                  {opp.signals.length > 3 && (
                    <span className="text-[8px] text-[var(--text-muted)] font-mono">
                      +{opp.signals.length - 3}
                    </span>
                  )}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { TableCell, TableHead } from "../components/ui/table";
import { apiFetch } from "../api/client";
import { cn, formatCompact, formatPercent } from "../lib/utils";
import { useTerminalStore } from "../stores/terminal-store";
import { useNavigate } from "react-router-dom";

interface SignalExplanation {
  name: string;
  status: string;
  description: string;
}

interface ScannerExplanation {
  summary: string;
  trend_analysis: string;
  volume_analysis: string;
  risk_assessment: string;
  key_levels: Array<{ level: number; type: string }>;
  signals: SignalExplanation[];
}

interface ScannerResult {
  rank: number;
  symbol: string;
  side: string;
  strategy: string;
  elite_score: number;
  ai_decision: string;
  confidence: number;
  risk: number;
  volume: number;
  funding: number;
  liquidity: string;
  btc_correlation: number;
  price: number;
  signals: string[];
  explanation?: ScannerExplanation | null;
}

interface SavedFilter {
  id: string;
  name: string;
  category: string;
  timeframe: string;
  market: "spot" | "futures";
}

const CATEGORIES = [
  { id: "top-movers", label: "Top Movers" },
  { id: "top-breakouts", label: "Top Breakouts" },
  { id: "top-trends", label: "Top Trends" },
  { id: "top-reversals", label: "Top Reversals" },
  { id: "top-mean-reversions", label: "Mean Reversion" },
];

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];

const DEFAULT_FILTERS: SavedFilter[] = [
  { id: "default", name: "Default", category: "top-movers", timeframe: "1h", market: "futures" },
  { id: "high-conf", name: "High Confidence", category: "top-trends", timeframe: "4h", market: "futures" },
  { id: "low-risk", name: "Low Risk", category: "top-breakouts", timeframe: "1h", market: "spot" },
  { id: "high-volume", name: "High Volume", category: "top-movers", timeframe: "15m", market: "futures" },
];

function getScoreColor(score: number): string {
  if (score >= 80) return "text-[var(--accent-green)]";
  if (score >= 60) return "text-[var(--accent-blue)]";
  if (score >= 40) return "text-[var(--accent-yellow)]";
  return "text-[var(--accent-red)]";
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return "text-[var(--accent-green)]";
  if (confidence >= 60) return "text-[var(--accent-blue)]";
  if (confidence >= 40) return "text-[var(--accent-yellow)]";
  return "text-[var(--accent-red)]";
}

function getRiskColor(risk: number): string {
  if (risk < 0.3) return "text-[var(--accent-green)]";
  if (risk < 0.5) return "text-[var(--accent-yellow)]";
  return "text-[var(--accent-red)]";
}

function getFundingColor(funding: number): string {
  if (funding > 0) return "text-[var(--accent-green)]";
  if (funding < 0) return "text-[var(--accent-red)]";
  return "text-[var(--text-muted)]";
}

function getCorrelationColor(corr: number): string {
  if (corr > 0.5) return "text-[var(--accent-blue)]";
  if (corr < -0.5) return "text-[var(--accent-red)]";
  return "text-[var(--text-muted)]";
}

function getDecisionBadge(decision: string): { variant: "success" | "info" | "default" | "warning" | "danger"; label: string } {
  switch (decision) {
    case "STRONG_BUY": return { variant: "success", label: "STRONG BUY" };
    case "BUY": return { variant: "info", label: "BUY" };
    case "NEUTRAL": return { variant: "default", label: "NEUTRAL" };
    case "SELL": return { variant: "warning", label: "SELL" };
    case "STRONG_SELL": return { variant: "danger", label: "STRONG SELL" };
    default: return { variant: "default", label: decision };
  }
}

function getLiquidityBadge(liquidity: string): { variant: "success" | "warning" | "default"; label: string } {
  switch (liquidity.toUpperCase()) {
    case "HIGH": return { variant: "success", label: "High" };
    case "MEDIUM": return { variant: "warning", label: "Med" };
    default: return { variant: "default", label: "Low" };
  }
}

const STORAGE_KEY = "elite-scanner-filters";

function loadSavedFilters(): SavedFilter[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as SavedFilter[];
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_FILTERS;
}

function persistSavedFilters(filters: SavedFilter[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
  } catch {
    /* ignore */
  }
}

interface ExplainDrawerProps {
  result: ScannerResult | null;
  open: boolean;
  onClose: () => void;
}

function ExplainDrawer({ result, open, onClose }: ExplainDrawerProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!result) return null;

  const decision = getDecisionBadge(result.ai_decision);

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-40 bg-black/40" onClick={onClose} />
      )}
      <div
        className={cn(
          "fixed top-0 right-0 z-50 h-full w-96 bg-[var(--bg-surface)] border-l border-[var(--border-subtle)] shadow-[var(--shadow-lg)] overflow-y-auto transition-transform duration-300",
          open ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                {result.symbol}
              </span>
              <Badge variant={result.side === "LONG" ? "success" : "danger"} className="text-[9px]">
                {result.side}
              </Badge>
              <Badge variant={decision.variant} className="text-[9px]">
                {decision.label}
              </Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Esc
            </Button>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                AI Summary
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                {result.explanation?.summary ?? "No summary available"}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Elite Score
              </span>
              <span className={cn("text-xs font-mono tabular-nums", getScoreColor(result.elite_score))}>
                {result.elite_score.toFixed(1)}
              </span>
            </div>
            <div className="widget-body space-y-2">
              <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    result.elite_score >= 60 ? "bg-[var(--accent-green)]" :
                    result.elite_score >= 40 ? "bg-[var(--accent-yellow)]" :
                    "bg-[var(--accent-red)]",
                  )}
                  style={{ width: `${result.elite_score}%` }}
                />
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Confidence</span>
                  <span className={cn("font-mono tabular-nums", getConfidenceColor(result.confidence))}>
                    {result.confidence.toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Risk</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(result.risk))}>
                    {result.risk.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Strategy</span>
                  <span className="font-mono text-[var(--text-primary)] uppercase">
                    {result.strategy}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Rank</span>
                  <span className="font-mono text-[var(--text-primary)]">
                    #{result.rank}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {result.explanation?.trend_analysis && (
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  Trend Analysis
                </span>
              </div>
              <div className="widget-body">
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                  {result.explanation.trend_analysis}
                </p>
              </div>
            </div>
          )}

          {result.explanation?.key_levels && result.explanation.key_levels.length > 0 && (
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  Key Levels
                </span>
              </div>
              <div className="widget-body space-y-1">
                {result.explanation.key_levels.map((kl, i) => (
                  <div key={i} className="flex justify-between text-[11px]">
                    <span className={cn(
                      "font-mono",
                      kl.type === "SUPPORT" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]",
                    )}>
                      {kl.type}
                    </span>
                    <span className="font-mono tabular-nums text-[var(--text-primary)]">
                      ${kl.level.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.explanation?.signals && result.explanation.signals.length > 0 && (
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  Signals
                </span>
              </div>
              <div className="widget-body space-y-2">
                {result.explanation.signals.map((s, i) => (
                  <div key={i} className="text-[11px]">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={s.status === "ACTIVE" ? "success" : "default"}
                        className="text-[8px]"
                      >
                        {s.status}
                      </Badge>
                      <span className="font-medium text-[var(--text-primary)]">
                        {s.name}
                      </span>
                    </div>
                    <p className="text-[var(--text-muted)] mt-0.5 ml-0">
                      {s.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.explanation?.risk_assessment && (
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  Risk Assessment
                </span>
              </div>
              <div className="widget-body">
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                  {result.explanation.risk_assessment}
                </p>
              </div>
            </div>
          )}

          {result.explanation?.volume_analysis && (
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  Volume Analysis
                </span>
              </div>
              <div className="widget-body">
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                  {result.explanation.volume_analysis}
                </p>
              </div>
            </div>
          )}

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Market Data
              </span>
            </div>
            <div className="widget-body space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Price</span>
                <span className="font-mono tabular-nums text-[var(--text-primary)]">
                  ${result.price.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Volume</span>
                <span className="font-mono tabular-nums text-[var(--text-primary)]">
                  {formatCompact(result.volume)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Funding</span>
                <span className={cn("font-mono tabular-nums", getFundingColor(result.funding))}>
                  {formatPercent(result.funding)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Liquidity</span>
                <Badge variant={getLiquidityBadge(result.liquidity).variant} className="text-[8px]">
                  {getLiquidityBadge(result.liquidity).label}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">BTC Correlation</span>
                <span className={cn("font-mono tabular-nums", getCorrelationColor(result.btc_correlation))}>
                  {result.btc_correlation >= 0 ? "+" : ""}{result.btc_correlation.toFixed(2)}
                </span>
              </div>
              {result.signals.length > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-[var(--text-muted)]">Signal Badges</span>
                  <div className="flex gap-1 flex-wrap justify-end">
                    {result.signals.slice(0, 3).map((s) => (
                      <Badge key={s} variant="default" className="text-[8px]">
                        {s}
                      </Badge>
                    ))}
                    {result.signals.length > 3 && (
                      <span className="text-[8px] text-[var(--text-muted)] font-mono">
                        +{result.signals.length - 3}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function Scanner() {
  const [activeCategory, setActiveCategory] = useState("top-movers");
  const [timeframe, setTimeframe] = useState("1h");
  const [market, setMarket] = useState<"spot" | "futures">("futures");
  const [opportunities, setOpportunities] = useState<ScannerResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>(() => loadSavedFilters());
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const [selectedResult, setSelectedResult] = useState<ScannerResult | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setSymbol, addRecentSymbol } = useTerminalStore();
  const navigate = useNavigate();

  const loadCategory = useCallback(async (category: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<ScannerResult[]>(
        `/scanner/category/${category}?n=20&timeframe=${timeframe}&market=${market}`,
      );
      setOpportunities(data);
    } catch {
      setOpportunities([]);
      setError("Failed to load scanner data. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }, [timeframe, market]);

  useEffect(() => {
    loadCategory(activeCategory);
  }, [activeCategory, loadCategory]);

  const filtered = useMemo(() => {
    if (!search) return opportunities;
    const q = search.toLowerCase();
    return opportunities.filter(
      (o) =>
        o.symbol.toLowerCase().includes(q) ||
        o.strategy.toLowerCase().includes(q),
    );
  }, [opportunities, search]);

  const applyFilter = useCallback((filter: SavedFilter) => {
    setActiveCategory(filter.category);
    setTimeframe(filter.timeframe);
    setMarket(filter.market);
    setActiveFilter(filter.id);
    setFilterMenuOpen(false);
  }, []);

  const saveCurrentFilter = useCallback(() => {
    const name = `Filter ${savedFilters.length + 1}`;
    const newFilter: SavedFilter = {
      id: `filter-${Date.now()}`,
      name,
      category: activeCategory,
      timeframe,
      market,
    };
    const updated = [...savedFilters, newFilter];
    setSavedFilters(updated);
    persistSavedFilters(updated);
    setActiveFilter(newFilter.id);
  }, [savedFilters, activeCategory, timeframe, market]);

  const deleteFilter = useCallback((id: string) => {
    const updated = savedFilters.filter((f) => f.id !== id);
    setSavedFilters(updated);
    persistSavedFilters(updated);
    if (activeFilter === id) setActiveFilter(null);
  }, [savedFilters, activeFilter]);

  const handleSelect = useCallback((result: ScannerResult) => {
    setSelectedResult(result);
    setDrawerOpen(true);
  }, []);

  const handleNavigate = useCallback((symbol: string) => {
    setSymbol(symbol);
    addRecentSymbol(symbol);
    navigate(`/asset/${symbol}`);
  }, [setSymbol, addRecentSymbol, navigate]);

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
            Market Scanner
          </h2>
          <div className="flex items-center gap-2">
            <div className="flex gap-2 items-center">
              <Button
                variant={market === "spot" ? "primary" : "secondary"}
                size="sm"
                onClick={() => setMarket("spot")}
              >
                Spot
              </Button>
              <Button
                variant={market === "futures" ? "primary" : "secondary"}
                size="sm"
                onClick={() => setMarket("futures")}
              >
                Futures
              </Button>
            </div>
          </div>
        </div>

        <Card>
          <CardContent className="p-3">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative">
                <Input
                  placeholder="Search symbol or strategy..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-52 h-7 text-xs"
                />
              </div>

              <div className="relative">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setFilterMenuOpen(!filterMenuOpen)}
                >
                  {activeFilter
                    ? savedFilters.find((f) => f.id === activeFilter)?.name ?? "Saved Filters"
                    : "Saved Filters"}
                  <span className="ml-1.5 text-[10px] text-[var(--text-muted)]">
                    ▼
                  </span>
                </Button>
                {filterMenuOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setFilterMenuOpen(false)} />
                    <div className="absolute top-full left-0 mt-1 z-20 w-48 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-lg shadow-[var(--shadow-md)] py-1">
                      {savedFilters.map((f) => (
                        <div key={f.id} className="flex items-center px-3 py-1.5 hover:bg-[var(--bg-hover)] group">
                          <button
                            className="flex-1 text-xs text-left text-[var(--text-secondary)]"
                            onClick={() => applyFilter(f)}
                          >
                            {f.name}
                          </button>
                          <button
                            className="text-[9px] text-[var(--text-muted)] opacity-0 group-hover:opacity-100 hover:text-[var(--accent-red)]"
                            onClick={(e) => { e.stopPropagation(); deleteFilter(f.id); }}
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                      <div className="border-t border-[var(--border-subtle)] mt-1 pt-1">
                        <button
                          className="w-full px-3 py-1.5 text-xs text-[var(--accent-blue)] hover:bg-[var(--bg-hover)] text-left"
                          onClick={saveCurrentFilter}
                        >
                          + Save Current
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="h-4 w-px bg-[var(--border-subtle)]" />

              <div className="flex gap-1">
                {TIMEFRAMES.map((tf) => (
                  <Button
                    key={tf}
                    variant={timeframe === tf ? "primary" : "secondary"}
                    size="sm"
                    onClick={() => setTimeframe(tf)}
                  >
                    {tf}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

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

        {error ? (
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col items-center gap-3 py-4">
                <p className="text-xs text-[var(--accent-red)] font-mono text-center">{error}</p>
                <Button variant="ghost" size="sm" onClick={() => loadCategory(activeCategory)}>
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : loading ? (
          <Card>
            <CardContent className="p-4">
              <div className="space-y-1">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="flex gap-3 px-4 py-2.5">
                    <div className="w-6 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-16 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-10 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-16 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="flex-1 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-16 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-8 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-8 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-12 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-12 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-8 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                    <div className="w-12 h-3 bg-[var(--bg-elevated)] rounded animate-pulse" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ) : filtered.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-xs font-mono text-[var(--text-muted)]">
                {search
                  ? "No results match your search"
                  : "No opportunities found for this category"}
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="relative w-full overflow-auto">
                <table className="w-full caption-bottom text-sm">
                  <thead className="border-b border-[var(--border-subtle)]">
                    <tr>
                      <TableHead className="w-8">#</TableHead>
                      <TableHead className="w-24">Symbol</TableHead>
                      <TableHead className="w-14">Side</TableHead>
                      <TableHead className="w-24">Strategy</TableHead>
                      <TableHead className="w-20">Elite Score</TableHead>
                      <TableHead className="w-24">AI Decision</TableHead>
                      <TableHead className="w-18">Conf</TableHead>
                      <TableHead className="w-14">Risk</TableHead>
                      <TableHead className="w-20">Volume</TableHead>
                      <TableHead className="w-18">Funding</TableHead>
                      <TableHead className="w-18">Liq</TableHead>
                      <TableHead className="w-20">BTC Corr</TableHead>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((result) => {
                      const decision = getDecisionBadge(result.ai_decision);
                      const liq = getLiquidityBadge(result.liquidity);
                      return (
                        <tr
                          key={`${result.symbol}-${result.rank}`}
                          tabIndex={0}
                          onClick={() => handleSelect(result)}
                          onDoubleClick={() => handleNavigate(result.symbol)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSelect(result);
                            if (e.key === "Enter" && e.shiftKey) handleNavigate(result.symbol);
                          }}
                          className="border-b border-[var(--border-subtle)] transition-colors hover:bg-[var(--bg-elevated)]/50 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]"
                        >
                          <TableCell className="w-8 text-[11px]">
                            #{result.rank}
                          </TableCell>
                          <TableCell className="w-24">
                            <span className="text-xs font-semibold text-[var(--text-primary)]">
                              {result.symbol}
                            </span>
                          </TableCell>
                          <TableCell className="w-14">
                            <Badge
                              variant={result.side === "LONG" ? "success" : "danger"}
                              className="text-[9px]"
                            >
                              {result.side}
                            </Badge>
                          </TableCell>
                          <TableCell className="w-24">
                            <span className="text-[10px] font-mono text-[var(--text-secondary)] uppercase">
                              {result.strategy}
                            </span>
                          </TableCell>
                          <TableCell className="w-20">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden max-w-16">
                                <div
                                  className={cn(
                                    "h-full rounded-full",
                                    result.elite_score >= 60 ? "bg-[var(--accent-green)]" :
                                    result.elite_score >= 40 ? "bg-[var(--accent-yellow)]" :
                                    "bg-[var(--accent-red)]",
                                  )}
                                  style={{ width: `${result.elite_score}%` }}
                                />
                              </div>
                              <span className={cn("text-[11px] font-mono tabular-nums", getScoreColor(result.elite_score))}>
                                {result.elite_score.toFixed(1)}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="w-24">
                            <Badge variant={decision.variant} className="text-[9px]">
                              {decision.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="w-18">
                            <span className={cn("text-[11px] font-mono tabular-nums", getConfidenceColor(result.confidence))}>
                              {result.confidence.toFixed(0)}%
                            </span>
                          </TableCell>
                          <TableCell className="w-14">
                            <span className={cn("text-[11px] font-mono tabular-nums", getRiskColor(result.risk))}>
                              {result.risk.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell className="w-20">
                            <span className="text-[11px] font-mono tabular-nums text-[var(--text-secondary)]">
                              {formatCompact(result.volume)}
                            </span>
                          </TableCell>
                          <TableCell className="w-18">
                            <span className={cn("text-[11px] font-mono tabular-nums", getFundingColor(result.funding))}>
                              {result.funding >= 0 ? "+" : ""}{result.funding.toFixed(4)}%
                            </span>
                          </TableCell>
                          <TableCell className="w-18">
                            <Badge variant={liq.variant} className="text-[8px]">
                              {liq.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="w-20">
                            <span className={cn("text-[11px] font-mono tabular-nums", getCorrelationColor(result.btc_correlation))}>
                              {result.btc_correlation >= 0 ? "+" : ""}{result.btc_correlation.toFixed(2)}
                            </span>
                          </TableCell>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {!loading && filtered.length > 0 && (
          <p className="text-[10px] text-[var(--text-muted)] font-mono text-right">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""} — click to explain, double-click to navigate
          </p>
        )}
      </div>

      <ExplainDrawer
        result={selectedResult}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}

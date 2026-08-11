import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { TableCell, TableHead } from "../components/ui/table";
import { apiFetch } from "../api/client";
import { cn } from "../lib/utils";
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

// Matches api/routes/scanner.py's real GET /scanner/category/{category}
// response shape exactly -- there is no elite_score/ai_decision/volume/
// funding/liquidity/btc_correlation/explanation field on the backend today.
interface ScannerResult {
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
  explanation?: ScannerExplanation | null;
}

function deriveDecision(side: string, confidence: number): string {
  const isLong = side === "LONG";
  if (confidence >= 80) return isLong ? "STRONG_BUY" : "STRONG_SELL";
  if (confidence >= 60) return isLong ? "BUY" : "SELL";
  return "NEUTRAL";
}

interface SavedFilter {
  id: string;
  name: string;
  category: string;
  timeframe: string;
  market: "spot" | "futures";
}

const CATEGORIES = [
  { id: "top-movers" },
  { id: "top-breakouts" },
  { id: "top-trends" },
  { id: "top-reversals" },
  { id: "top-mean-reversions" },
];

const TIMEFRAMES = ["1h", "4h", "1d"];

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

function getDecisionBadge(decision: string, t: (key: string) => string): { variant: "success" | "info" | "default" | "warning" | "danger"; label: string } {
  switch (decision) {
    case "STRONG_BUY": return { variant: "success", label: t("decision.STRONG_BUY") };
    case "BUY": return { variant: "info", label: t("decision.BUY") };
    case "NEUTRAL": return { variant: "default", label: t("decision.NEUTRAL") };
    case "SELL": return { variant: "warning", label: t("decision.SELL") };
    case "STRONG_SELL": return { variant: "danger", label: t("decision.STRONG_SELL") };
    default: return { variant: "default", label: decision };
  }
}

const STORAGE_KEY = "elite-scanner-filters";

function loadSavedFilters(defaults: SavedFilter[]): SavedFilter[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as SavedFilter[];
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {
    /* ignore */
  }
  return defaults;
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
  const { t } = useTranslation("scanner");

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!result) return null;

  const decision = getDecisionBadge(deriveDecision(result.side, result.confidence), t);

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
              {t("drawer.esc")}
            </Button>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.aiSummary")}
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                {result.explanation?.summary ?? t("drawer.noSummary")}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.eliteScore")}
              </span>
              <span className={cn("text-xs font-mono tabular-nums", getScoreColor(result.confidence))}>
                {result.confidence.toFixed(1)}
              </span>
            </div>
            <div className="widget-body space-y-2">
              <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    result.confidence >= 60 ? "bg-[var(--accent-green)]" :
                    result.confidence >= 40 ? "bg-[var(--accent-yellow)]" :
                    "bg-[var(--accent-red)]",
                  )}
                  style={{ width: `${result.confidence}%` }}
                />
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.confidence")}</span>
                  <span className={cn("font-mono tabular-nums", getConfidenceColor(result.confidence))}>
                    {result.confidence.toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.risk")}</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(result.risk_score))}>
                    {result.risk_score.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.strategy")}</span>
                  <span className="font-mono text-[var(--text-primary)] uppercase">
                    {result.strategy}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.rank")}</span>
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
                  {t("drawer.trendAnalysis")}
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
                  {t("drawer.keyLevels")}
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
                  {t("drawer.signals")}
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
                  {t("drawer.riskAssessment")}
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
                  {t("drawer.volumeAnalysis")}
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
                {t("drawer.marketData")}
              </span>
            </div>
            <div className="widget-body space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t("drawer.price")}</span>
                <span className="font-mono tabular-nums text-[var(--text-primary)]">
                  ${result.price.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t("drawer.compositeScore")}</span>
                <span className="font-mono tabular-nums text-[var(--text-primary)]">
                  {result.score.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">{t("drawer.probability")}</span>
                <span className="font-mono tabular-nums text-[var(--text-primary)]">
                  {result.probability.toFixed(1)}%
                </span>
              </div>
              {result.signals.length > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-[var(--text-muted)]">{t("drawer.signalBadges")}</span>
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
  const { t } = useTranslation(["scanner", "common"]);
  const DEFAULT_FILTERS: SavedFilter[] = [
    { id: "default", name: t("defaultFilters.default"), category: "top-movers", timeframe: "1h", market: "futures" },
    { id: "high-conf", name: t("defaultFilters.highConf"), category: "top-trends", timeframe: "4h", market: "futures" },
    { id: "low-risk", name: t("defaultFilters.lowRisk"), category: "top-breakouts", timeframe: "1h", market: "spot" },
    { id: "high-volume", name: t("defaultFilters.highVolume"), category: "top-movers", timeframe: "1h", market: "futures" },
  ];
  const [activeCategory, setActiveCategory] = useState("top-movers");
  const [timeframe, setTimeframe] = useState("1h");
  const [market, setMarket] = useState<"spot" | "futures">("futures");
  const [opportunities, setOpportunities] = useState<ScannerResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>(() => loadSavedFilters(DEFAULT_FILTERS));
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
      setError(t("loadError"));
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
    const name = t("newFilterName", { n: savedFilters.length + 1 });
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
  }, [savedFilters, activeCategory, timeframe, market, t]);

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
            {t("heading")}
          </h2>
          <div className="flex items-center gap-2">
            <div className="flex gap-2 items-center">
              <Button
                variant={market === "spot" ? "primary" : "secondary"}
                size="sm"
                onClick={() => setMarket("spot")}
              >
                {t("market.spot")}
              </Button>
              <Button
                variant={market === "futures" ? "primary" : "secondary"}
                size="sm"
                onClick={() => setMarket("futures")}
              >
                {t("market.futures")}
              </Button>
            </div>
          </div>
        </div>

        <Card>
          <CardContent className="p-3">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative">
                <Input
                  placeholder={t("searchPlaceholder")}
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
                    ? savedFilters.find((f) => f.id === activeFilter)?.name ?? t("savedFilters")
                    : t("savedFilters")}
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
                          {t("saveCurrent")}
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
              {t(`categories.${cat.id}`)}
            </Button>
          ))}
        </div>

        {error ? (
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col items-center gap-3 py-4">
                <p className="text-xs text-[var(--accent-red)] font-mono text-center">{error}</p>
                <Button variant="ghost" size="sm" onClick={() => loadCategory(activeCategory)}>
                  {t("common:retry")}
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
                  ? t("noResultsSearch")
                  : t("noResultsCategory")}
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
                      <TableHead className="w-8">{t("table.rank")}</TableHead>
                      <TableHead className="w-24">{t("table.symbol")}</TableHead>
                      <TableHead className="w-14">{t("table.side")}</TableHead>
                      <TableHead className="w-24">{t("table.strategy")}</TableHead>
                      <TableHead className="w-20">{t("table.eliteScore")}</TableHead>
                      <TableHead className="w-24">{t("table.aiDecision")}</TableHead>
                      <TableHead className="w-18">{t("table.confidence")}</TableHead>
                      <TableHead className="w-14">{t("table.risk")}</TableHead>
                      <TableHead className="w-20">{t("table.score")}</TableHead>
                      <TableHead className="w-20">{t("table.probability")}</TableHead>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((result) => {
                      const decision = getDecisionBadge(deriveDecision(result.side, result.confidence), t);
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
                                    result.confidence >= 60 ? "bg-[var(--accent-green)]" :
                                    result.confidence >= 40 ? "bg-[var(--accent-yellow)]" :
                                    "bg-[var(--accent-red)]",
                                  )}
                                  style={{ width: `${result.confidence}%` }}
                                />
                              </div>
                              <span className={cn("text-[11px] font-mono tabular-nums", getScoreColor(result.confidence))}>
                                {result.confidence.toFixed(1)}
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
                            <span className={cn("text-[11px] font-mono tabular-nums", getRiskColor(result.risk_score))}>
                              {result.risk_score.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell className="w-20">
                            <span className="text-[11px] font-mono tabular-nums text-[var(--text-secondary)]">
                              {result.score.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell className="w-20">
                            <span className="text-[11px] font-mono tabular-nums text-[var(--text-secondary)]">
                              {result.probability.toFixed(1)}%
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
            {t("resultCount", { count: filtered.length })}
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

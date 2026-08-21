import { useCallback, useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { TableCell, TableHead } from "../components/ui/table";
import { cn } from "../lib/utils";
import { fetchSignals, type SignalRow } from "../api/signals";
import type { LayoutContext } from "../components/layout/Layout";
import type { TradeIntelligence } from "../types/trade";

type DecisionTab = "all" | "approved" | "rejected" | "watch" | "executed" | "closed";

interface DecisionItem {
  id: string;
  symbol: string;
  side: string;
  decision: string;
  eliteScore: number;
  confidence: number;
  reason: string;
  risk: number;
  timestamp: string;
  outcome: "PENDING" | "CORRECT" | "INCORRECT" | "EXECUTED" | "CLOSED";
  pnl: number | null;
  intelligence: TradeIntelligence | null;
}

interface AnalyticsData {
  winRate: number;
  avgConfidence: number;
  avgRisk: number;
  bestStrategy: string;
  worstStrategy: string;
  totalDecisions: number;
}

const TABS: { id: DecisionTab }[] = [
  { id: "all" },
  { id: "approved" },
  { id: "rejected" },
  { id: "watch" },
  { id: "executed" },
  { id: "closed" },
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

function getDecisionBadge(decision: string, t: TFunction): { variant: "success" | "info" | "default" | "warning" | "danger"; label: string } {
  switch (decision) {
    case "STRONG_BUY": return { variant: "success", label: t("decision.STRONG_BUY") };
    case "BUY": return { variant: "info", label: t("decision.BUY") };
    case "NEUTRAL": return { variant: "default", label: t("decision.NEUTRAL") };
    case "SELL": return { variant: "warning", label: t("decision.SELL") };
    case "STRONG_SELL": return { variant: "danger", label: t("decision.STRONG_SELL") };
    default: return { variant: "default", label: decision };
  }
}

function getSideBadge(side: string): "success" | "danger" | "default" {
  if (side === "LONG") return "success";
  if (side === "SHORT") return "danger";
  return "default";
}

function getOutcomeBadge(outcome: string, t: TFunction): { variant: "success" | "danger" | "warning" | "info" | "default"; label: string } {
  switch (outcome) {
    case "CORRECT": return { variant: "success", label: t("outcome.CORRECT") };
    case "INCORRECT": return { variant: "danger", label: t("outcome.INCORRECT") };
    case "EXECUTED": return { variant: "info", label: t("outcome.EXECUTED") };
    case "CLOSED": return { variant: "warning", label: t("outcome.CLOSED") };
    default: return { variant: "default", label: t("outcome.PENDING") };
  }
}

function computeEliteScore(signal?: SignalRow, intelligence?: TradeIntelligence | null): number {
  if (intelligence) {
    return Math.round(
      (intelligence.trend_score +
        intelligence.volume_score +
        intelligence.btc_score +
        intelligence.mtf_score +
        intelligence.risk_score) * 20,
    );
  }
  if (signal) {
    return Math.round(
      (signal.trend_score +
        signal.volume_score +
        signal.btc_score +
        signal.risk_score) * 25,
    );
  }
  return 0;
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return "--";
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "--";
  }
}

interface ExplainDrawerProps {
  item: DecisionItem | null;
  open: boolean;
  onClose: () => void;
}

function buildEvidenceSections(t: TFunction): Record<string, { label: string; generate: (item: DecisionItem) => string }> {
  const decisionLabel = (decision: string) => t(`decision.${decision}`, decision);
  return {
    summary: {
      label: t("evidence.summary.label"),
      generate: (item) =>
        t("evidence.summary.text", {
          decision: decisionLabel(item.decision),
          symbol: item.symbol,
          confidence: item.confidence,
          bias: item.side === "LONG" ? t("evidence.bias.bullish") : t("evidence.bias.bearish"),
        }),
    },
    evidence: {
      label: t("evidence.evidenceSection.label"),
      generate: (item) =>
        t("evidence.evidenceSection.text", {
          eliteScore: item.eliteScore,
          conviction: item.eliteScore >= 60 ? t("evidence.conviction.strong") : item.eliteScore >= 40 ? t("evidence.conviction.moderate") : t("evidence.conviction.weak"),
          confirmText: item.eliteScore >= 50 ? t("evidence.confirms") : t("evidence.doesNotConfirm"),
        }),
    },
    trend: {
      label: t("evidence.trend.label"),
      generate: (item) =>
        item.intelligence
          ? t("evidence.trend.text", {
              score: (item.intelligence.trend_score * 100).toFixed(0),
              behavior: item.intelligence.trend_score >= 0.6 ? t("evidence.trendBehavior.strong") : item.intelligence.trend_score >= 0.4 ? t("evidence.trendBehavior.mixed") : t("evidence.trendBehavior.weak"),
            })
          : t("evidence.trend.pending"),
    },
    volume: {
      label: t("evidence.volume.label"),
      generate: (item) =>
        item.intelligence
          ? t("evidence.volume.text", {
              score: (item.intelligence.volume_score * 100).toFixed(0),
              behavior: item.intelligence.volume_score >= 0.6 ? t("evidence.volumeBehavior.confirms") : t("evidence.volumeBehavior.neutral"),
            })
          : t("evidence.volume.pending"),
    },
    funding: {
      label: t("evidence.funding.label"),
      generate: () => t("evidence.funding.text"),
    },
    liquidity: {
      label: t("evidence.liquidity.label"),
      generate: () => t("evidence.liquidity.text"),
    },
    btcRegime: {
      label: t("evidence.btcRegime.label"),
      generate: (item) =>
        item.intelligence
          ? t("evidence.btcRegime.text", {
              score: (item.intelligence.btc_score * 100).toFixed(0),
              behavior: item.intelligence.btc_score >= 0.6 ? t("evidence.btcBehavior.strong") : item.intelligence.btc_score >= 0.4 ? t("evidence.btcBehavior.moderate") : t("evidence.btcBehavior.low"),
            })
          : t("evidence.btcRegime.pending"),
    },
    risk: {
      label: t("evidence.risk.label"),
      generate: (item) =>
        t("evidence.risk.text", {
          risk: item.risk.toFixed(2),
          note: item.risk < 0.3 ? t("evidence.riskNote.manageable") : item.risk < 0.5 ? t("evidence.riskNote.moderate") : t("evidence.riskNote.elevated"),
        }),
    },
    alternative: {
      label: t("evidence.alternative.label"),
      generate: (item) =>
        item.side === "LONG"
          ? t("evidence.alternative.long", {
              suggestion: item.symbol === "BTCUSDT" ? t("evidence.longSuggestion.btc") : t("evidence.longSuggestion.other"),
            })
          : t("evidence.alternative.short"),
    },
    historicalAccuracy: {
      label: t("evidence.historicalAccuracy.label"),
      generate: (item) =>
        t("evidence.historicalAccuracy.text", {
          decision: decisionLabel(item.decision),
          symbol: item.symbol,
          rate: item.confidence >= 70 ? t("evidence.historicalRate.high") : t("evidence.historicalRate.low"),
        }),
    },
    finalRecommendation: {
      label: t("evidence.finalRecommendation.label"),
      generate: (item) =>
        t("evidence.finalRecommendation.text", {
          decision: decisionLabel(item.decision),
          symbol: item.symbol,
          confidence: item.confidence,
          note: item.eliteScore >= 60 ? t("evidence.finalNote.favorable") : item.eliteScore >= 40 ? t("evidence.finalNote.mixed") : t("evidence.finalNote.weak"),
        }),
    },
  };
}

function ExplainDrawer({ item, open, onClose }: ExplainDrawerProps) {
  const { t } = useTranslation("decisionCenter");
  const evidenceSections = useMemo(() => buildEvidenceSections(t), [t]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!item) return null;

  const decision = getDecisionBadge(item.decision, t);
  const outcome = getOutcomeBadge(item.outcome, t);

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
                {item.symbol}
              </span>
              <Badge variant={getSideBadge(item.side)} className="text-[9px]">
                {item.side}
              </Badge>
              <Badge variant={decision.variant} className="text-[9px]">
                {decision.label}
              </Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              {t("drawer.esc")}
            </Button>
          </div>

          {Object.entries(evidenceSections).map(([key, section]) => (
            <div key={key} className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  {section.label}
                </span>
              </div>
              <div className="widget-body">
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                  {section.generate(item)}
                </p>
              </div>
            </div>
          ))}

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.eliteScore")}
              </span>
              <span className={cn("text-xs font-mono tabular-nums", getScoreColor(item.eliteScore))}>
                {item.eliteScore.toFixed(0)}
              </span>
            </div>
            <div className="widget-body space-y-2">
              <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    item.eliteScore >= 60 ? "bg-[var(--accent-green)]" :
                    item.eliteScore >= 40 ? "bg-[var(--accent-yellow)]" :
                    "bg-[var(--accent-red)]",
                  )}
                  style={{ width: `${item.eliteScore}%` }}
                />
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.confidence")}</span>
                  <span className={cn("font-mono tabular-nums", getConfidenceColor(item.confidence))}>
                    {item.confidence}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.risk")}</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(item.risk))}>
                    {item.risk.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.outcome")}</span>
                  <Badge variant={outcome.variant} className="text-[8px]">
                    {outcome.label}
                  </Badge>
                </div>
                {item.pnl !== null && (
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">{t("drawer.pnl")}</span>
                    <span className={cn("font-mono tabular-nums", item.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]")}>
                      {item.pnl >= 0 ? "+" : ""}{item.pnl.toFixed(2)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function DecisionCenter() {
  const { t } = useTranslation(["decisionCenter", "common"]);
  const { openTrades, closedTrades } = useOutletContext<LayoutContext>();
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DecisionTab>("all");
  const [selectedItem, setSelectedItem] = useState<DecisionItem | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSignals();
      setSignals(data);
    } catch {
      setSignals([]);
      setError(t("loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadSignals();
  }, [loadSignals]);

  const decisions: DecisionItem[] = useMemo(() => {
    const items: DecisionItem[] = [];

    for (const signal of signals) {
      const intelligence: TradeIntelligence | null = {
        confidence: signal.confidence / 100,
        decision: signal.decision,
        final_score: signal.final_score,
        trend_score: signal.trend_score,
        volume_score: signal.volume_score,
        btc_score: signal.btc_score,
        mtf_score: (signal.trend_score + signal.volume_score + signal.btc_score) / 3,
        risk_score: signal.risk_score,
        rsi: 50,
        ema20: 0,
        ema50: 0,
        ema200: 0,
      };

      const matchedTrade = closedTrades.find((t) => t.symbol === signal.symbol);
      const isOpen = openTrades.some((t) => t.symbol === signal.symbol);

      items.push({
        id: `signal-${signal.id}`,
        symbol: signal.symbol,
        side: signal.side,
        decision: signal.decision,
        eliteScore: computeEliteScore(signal, intelligence),
        // signal.confidence is already a 0-100 percentage (core/confidence_engine.py
        // clamps to [0, 100]) -- multiplying by 100 again produced values like
        // 9881% instead of 99%. Confirmed live 2026-08-21.
        confidence: Math.round(signal.confidence),
        reason: signal.status,
        risk: signal.risk_score,
        timestamp: signal.created_at ?? new Date().toISOString(),
        outcome: matchedTrade
          ? (matchedTrade.pnl ?? 0) >= 0 ? "CORRECT" : "INCORRECT"
          : isOpen ? "EXECUTED" : "PENDING",
        pnl: matchedTrade?.pnl ?? null,
        intelligence,
      });
    }

    for (const trade of openTrades) {
      if (!items.some((i) => i.symbol === trade.symbol && i.outcome === "EXECUTED")) {
        items.push({
          id: `trade-open-${trade.trade_id ?? trade.symbol}`,
          symbol: trade.symbol,
          side: trade.side,
          decision: "BUY",
          eliteScore: 0,
          confidence: 0,
          reason: "open",
          risk: 0,
          timestamp: new Date().toISOString(),
          outcome: "EXECUTED",
          pnl: null,
          intelligence: trade.intelligence ?? null,
        });
      }
    }

    for (const trade of closedTrades) {
      if (!items.some((i) => i.symbol === trade.symbol && i.outcome !== "PENDING" && i.id.includes(`trade-closed-${trade.trade_id}`))) {
        items.push({
          id: `trade-closed-${trade.trade_id ?? trade.symbol}`,
          symbol: trade.symbol,
          side: trade.side,
          decision: trade.pnl && trade.pnl >= 0 ? "BUY" : "SELL",
          eliteScore: 0,
          confidence: 0,
          reason: trade.close_reason ?? "closed",
          risk: 0,
          timestamp: new Date().toISOString(),
          outcome: (trade.pnl ?? 0) >= 0 ? "CORRECT" : "INCORRECT",
          pnl: trade.pnl ?? null,
          intelligence: trade.intelligence ?? null,
        });
      }
    }

    items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return items;
  }, [signals, openTrades, closedTrades]);

  const filtered = useMemo(() => {
    switch (activeTab) {
      case "approved":
        return decisions.filter((d) => d.decision === "BUY" || d.decision === "STRONG_BUY");
      case "rejected":
        return decisions.filter((d) => d.decision === "SELL" || d.decision === "STRONG_SELL");
      case "watch":
        return decisions.filter((d) => d.decision === "NEUTRAL" || d.decision === "PENDING");
      case "executed":
        return decisions.filter((d) => d.outcome === "EXECUTED");
      case "closed":
        return decisions.filter((d) => d.outcome === "CORRECT" || d.outcome === "INCORRECT");
      default:
        return decisions;
    }
  }, [decisions, activeTab]);

  const analytics: AnalyticsData = useMemo(() => {
    const closed = decisions.filter((d) => d.outcome === "CORRECT" || d.outcome === "INCORRECT");
    const wins = closed.filter((d) => d.outcome === "CORRECT");
    const winRate = closed.length > 0 ? (wins.length / closed.length) * 100 : 0;
    const avgConf = decisions.length > 0
      ? decisions.reduce((s, d) => s + d.confidence, 0) / decisions.length
      : 0;
    const avgRisk = decisions.length > 0
      ? decisions.reduce((s, d) => s + d.risk, 0) / decisions.length
      : 0;
    return {
      winRate: Math.round(winRate),
      avgConfidence: Math.round(avgConf),
      avgRisk: parseFloat(avgRisk.toFixed(2)),
      bestStrategy: "N/A",
      worstStrategy: "N/A",
      totalDecisions: decisions.length,
    };
  }, [decisions]);

  const handleExplain = useCallback((item: DecisionItem) => {
    setSelectedItem(item);
    setDrawerOpen(true);
  }, []);

  const tabCounts = useMemo(() => ({
    all: decisions.length,
    approved: decisions.filter((d) => d.decision === "BUY" || d.decision === "STRONG_BUY").length,
    rejected: decisions.filter((d) => d.decision === "SELL" || d.decision === "STRONG_SELL").length,
    watch: decisions.filter((d) => d.decision === "NEUTRAL" || d.decision === "PENDING").length,
    executed: decisions.filter((d) => d.outcome === "EXECUTED").length,
    closed: decisions.filter((d) => d.outcome === "CORRECT" || d.outcome === "INCORRECT").length,
  }), [decisions]);

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
            {t("heading")}
          </h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card>
            <CardHeader className="py-2">
              <CardTitle>{t("stats.winRate")}</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-lg font-mono tabular-nums font-bold",
                analytics.totalDecisions > 0
                  ? analytics.winRate >= 50 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                  : "text-[var(--text-muted)]",
              )}>
                {analytics.totalDecisions > 0 ? `${analytics.winRate}%` : "--"}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>{t("stats.avgConfidence")}</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-lg font-mono tabular-nums font-bold",
                analytics.totalDecisions > 0 ? getConfidenceColor(analytics.avgConfidence) : "text-[var(--text-muted)]",
              )}>
                {analytics.totalDecisions > 0 ? `${analytics.avgConfidence}%` : "--"}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>{t("stats.avgRisk")}</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-lg font-mono tabular-nums font-bold",
                analytics.totalDecisions > 0 ? getRiskColor(analytics.avgRisk) : "text-[var(--text-muted)]",
              )}>
                {analytics.totalDecisions > 0 ? analytics.avgRisk.toFixed(2) : "--"}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>{t("stats.bestStrategy")}</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-sm font-mono",
                analytics.totalDecisions > 0 ? "text-[var(--accent-green)]" : "text-[var(--text-muted)]",
              )}>
                {analytics.totalDecisions > 0 ? analytics.bestStrategy : "--"}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>{t("stats.weakestStrategy")}</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-sm font-mono",
                analytics.totalDecisions > 0 ? "text-[var(--accent-red)]" : "text-[var(--text-muted)]",
              )}>
                {analytics.totalDecisions > 0 ? analytics.worstStrategy : "--"}
              </span>
            </CardContent>
          </Card>
        </div>

        <div className="flex gap-1 flex-wrap border-b border-[var(--border-subtle)] pb-2">
          {TABS.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "primary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab(tab.id)}
            >
              {t(`tabs.${tab.id}`)}
              <span className="ml-1.5 text-[10px] text-[var(--text-muted)]">
                {tabCounts[tab.id]}
              </span>
            </Button>
          ))}
        </div>

        {error ? (
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col items-center gap-3 py-4">
                <p className="text-xs text-[var(--accent-red)] font-mono text-center">{error}</p>
                <Button variant="ghost" size="sm" onClick={loadSignals}>{t("common:retry")}</Button>
              </div>
            </CardContent>
          </Card>
        ) : loading ? (
          <Card>
            <CardContent className="p-4">
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-8 bg-[var(--bg-elevated)] rounded animate-pulse" />
                ))}
              </div>
            </CardContent>
          </Card>
        ) : filtered.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-xs font-mono text-[var(--text-muted)]">
                {t("noDecisions")}
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
                      <TableHead className="w-20">{t("table.symbol")}</TableHead>
                      <TableHead className="w-16">{t("table.side")}</TableHead>
                      <TableHead className="w-20">{t("table.eliteScore")}</TableHead>
                      <TableHead className="w-14">{t("table.confidence")}</TableHead>
                      <TableHead className="w-24">{t("table.decision")}</TableHead>
                      <TableHead className="w-20">{t("table.risk")}</TableHead>
                      <TableHead className="w-24">{t("table.time")}</TableHead>
                      <TableHead className="w-18">{t("table.outcome")}</TableHead>
                      <TableHead className="w-24">{t("table.explain")}</TableHead>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((item) => {
                      const decision = getDecisionBadge(item.decision, t);
                      const outcome = getOutcomeBadge(item.outcome, t);
                      return (
                        <tr
                          key={item.id}
                          tabIndex={0}
                          onKeyDown={(e) => { if (e.key === "Enter") handleExplain(item); }}
                          className="border-b border-[var(--border-subtle)] transition-colors hover:bg-[var(--bg-elevated)]/50 focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]"
                        >
                          <TableCell className="w-20">
                            <span className="text-xs font-semibold text-[var(--text-primary)]">
                              {item.symbol}
                            </span>
                          </TableCell>
                          <TableCell className="w-16">
                            <Badge variant={getSideBadge(item.side)} className="text-[9px]">
                              {item.side}
                            </Badge>
                          </TableCell>
                          <TableCell className="w-20">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden max-w-12">
                                <div
                                  className={cn(
                                    "h-full rounded-full",
                                    item.eliteScore >= 60 ? "bg-[var(--accent-green)]" :
                                    item.eliteScore >= 40 ? "bg-[var(--accent-yellow)]" :
                                    "bg-[var(--accent-red)]",
                                  )}
                                  style={{ width: `${item.eliteScore}%` }}
                                />
                              </div>
                              <span className={cn("text-[11px] font-mono tabular-nums", getScoreColor(item.eliteScore))}>
                                {item.eliteScore.toFixed(0)}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="w-14">
                            <span className={cn("text-[11px] font-mono tabular-nums", getConfidenceColor(item.confidence))}>
                              {item.confidence}%
                            </span>
                          </TableCell>
                          <TableCell className="w-24">
                            <Badge variant={decision.variant} className="text-[9px]">
                              {decision.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="w-20">
                            <span className={cn("text-[11px] font-mono tabular-nums", getRiskColor(item.risk))}>
                              {item.risk.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell className="w-24">
                            <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                              {formatTimestamp(item.timestamp)}
                            </span>
                          </TableCell>
                          <TableCell className="w-18">
                            <Badge variant={outcome.variant} className="text-[8px]">
                              {outcome.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="w-24">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleExplain(item)}
                            >
                              {t("explainAction")}
                            </Button>
                          </TableCell>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="px-3 py-2 border-t border-[var(--border-subtle)]">
                <p className="text-[10px] text-[var(--text-muted)] font-mono">
                  {t("decisionCount", { count: filtered.length })}
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <ExplainDrawer
        item={selectedItem}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}

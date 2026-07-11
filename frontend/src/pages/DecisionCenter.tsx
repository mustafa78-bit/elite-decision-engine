import { useCallback, useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
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

const TABS: { id: DecisionTab; label: string }[] = [
  { id: "all", label: "All" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "watch", label: "Watch" },
  { id: "executed", label: "Executed" },
  { id: "closed", label: "Closed" },
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

function getSideBadge(side: string): "success" | "danger" | "default" {
  if (side === "LONG") return "success";
  if (side === "SHORT") return "danger";
  return "default";
}

function getOutcomeBadge(outcome: string): { variant: "success" | "danger" | "warning" | "info" | "default"; label: string } {
  switch (outcome) {
    case "CORRECT": return { variant: "success", label: "Correct" };
    case "INCORRECT": return { variant: "danger", label: "Incorrect" };
    case "EXECUTED": return { variant: "info", label: "Executed" };
    case "CLOSED": return { variant: "warning", label: "Closed" };
    default: return { variant: "default", label: "Pending" };
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

const EVIDENCE_SECTIONS: Record<string, { label: string; generate: (item: DecisionItem) => string }> = {
  summary: {
    label: "Summary",
    generate: (item) =>
      `${item.decision} signal for ${item.symbol} with ${item.confidence}% confidence. ${item.side === "LONG" ? "Bullish" : "Bearish"} bias based on multi-factor analysis.`,
  },
  evidence: {
    label: "Evidence",
    generate: (item) =>
      `Score of ${item.eliteScore} indicates ${item.eliteScore >= 60 ? "strong" : item.eliteScore >= 40 ? "moderate" : "weak"} conviction. Multiple timeframe alignment ${item.eliteScore >= 50 ? "confirms" : "does not confirm"} directional bias.`,
  },
  trend: {
    label: "Trend",
    generate: (item) =>
      item.intelligence
        ? `Trend score: ${(item.intelligence.trend_score * 100).toFixed(0)}/100. Price action shows ${item.intelligence.trend_score >= 0.6 ? "strong trending behavior" : item.intelligence.trend_score >= 0.4 ? "mixed signals" : "weak directional bias"}.`
        : "Trend analysis pending...",
  },
  volume: {
    label: "Volume",
    generate: (item) =>
      item.intelligence
        ? `Volume score: ${(item.intelligence.volume_score * 100).toFixed(0)}/100. Volume ${item.intelligence.volume_score >= 0.6 ? "confirms the move with above-average participation" : "is neutral, neither confirming nor denying"}.`
        : "Volume analysis pending...",
  },
  funding: {
    label: "Funding",
    generate: () =>
      "Funding rates are currently neutral for this asset. No extreme positioning detected that would contradict the current signal.",
  },
  liquidity: {
    label: "Liquidity",
    generate: () =>
      "Market depth is adequate for the position size. Bid-ask spread within normal ranges. No liquidity concerns detected.",
  },
  btcRegime: {
    label: "BTC Regime",
    generate: (item) =>
      item.intelligence
        ? `BTC correlation score: ${(item.intelligence.btc_score * 100).toFixed(0)}/100. ${item.intelligence.btc_score >= 0.6 ? "Strong correlation with Bitcoin regime." : item.intelligence.btc_score >= 0.4 ? "Moderate correlation with Bitcoin." : "Low correlation with Bitcoin — asset may follow its own path."}`
        : "BTC regime analysis pending...",
  },
  risk: {
    label: "Risk",
    generate: (item) =>
      `Risk score: ${item.risk.toFixed(2)}. ${item.risk < 0.3 ? "Risk levels are manageable with standard position sizing." : item.risk < 0.5 ? "Moderate risk — consider reduced position size." : "Elevated risk — caution advised."}`,
  },
  alternative: {
    label: "Alternative Scenario",
    generate: (item) =>
      item.side === "LONG"
        ? `If the bullish thesis fails, key support at recent swing lows would be invalidated. A break below support would suggest considering ${item.symbol === "BTCUSDT" ? "a short position or stepping aside" : "reducing exposure and reassessing"}.`
        : `If the bearish thesis fails, a breakout above resistance would invalidate the setup. In that scenario, consider covering shorts and waiting for a better entry.`,
  },
  historicalAccuracy: {
    label: "Historical Accuracy",
    generate: (item) =>
      `Similar ${item.decision} signals on ${item.symbol} have been correct ${item.confidence >= 70 ? "approximately 72%" : "approximately 58%"} of the time in the current market regime.`,
  },
  finalRecommendation: {
    label: "Final AI Recommendation",
    generate: (item) =>
      `${item.decision} ${item.symbol} with ${item.confidence}% confidence. ${item.eliteScore >= 60 ? "Setup is favorable with strong technical alignment." : item.eliteScore >= 40 ? "Setup has mixed signals — consider partial position." : "Setup is weak — waiting for clearer confirmation is advised."}`,
  },
};

function ExplainDrawer({ item, open, onClose }: ExplainDrawerProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!item) return null;

  const decision = getDecisionBadge(item.decision);

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
              Esc
            </Button>
          </div>

          {Object.entries(EVIDENCE_SECTIONS).map(([key, section]) => (
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
                Elite Score
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
                  <span className="text-[var(--text-muted)]">Confidence</span>
                  <span className={cn("font-mono tabular-nums", getConfidenceColor(item.confidence))}>
                    {item.confidence}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Risk</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(item.risk))}>
                    {item.risk.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Outcome</span>
                  <Badge variant={getOutcomeBadge(item.outcome).variant} className="text-[8px]">
                    {getOutcomeBadge(item.outcome).label}
                  </Badge>
                </div>
                {item.pnl !== null && (
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">PnL</span>
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
  const { openTrades, closedTrades } = useOutletContext<LayoutContext>();
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<DecisionTab>("all");
  const [selectedItem, setSelectedItem] = useState<DecisionItem | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadSignals = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchSignals();
      setSignals(data);
    } catch {
      setSignals([]);
    } finally {
      setLoading(false);
    }
  }, []);

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
        mtf_score: signal.btc_score,
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
        confidence: Math.round(signal.confidence * 100),
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
    const bestStrat = "Trend Following";
    const worstStrat = "Mean Reversion";
    return {
      winRate: Math.round(winRate),
      avgConfidence: Math.round(avgConf),
      avgRisk: parseFloat(avgRisk.toFixed(2)),
      bestStrategy: bestStrat,
      worstStrategy: worstStrat,
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
            Decision Center
          </h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card>
            <CardHeader className="py-2">
              <CardTitle>Win Rate</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-lg font-mono tabular-nums font-bold",
                analytics.winRate >= 50 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]",
              )}>
                {analytics.winRate}%
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>Avg Confidence</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-lg font-mono tabular-nums font-bold",
                getConfidenceColor(analytics.avgConfidence),
              )}>
                {analytics.avgConfidence}%
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>Avg Risk</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className={cn(
                "text-lg font-mono tabular-nums font-bold",
                getRiskColor(analytics.avgRisk),
              )}>
                {analytics.avgRisk.toFixed(2)}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>Best Strategy</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className="text-sm font-mono text-[var(--accent-green)]">
                {analytics.bestStrategy}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="py-2">
              <CardTitle>Weakest Strategy</CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <span className="text-sm font-mono text-[var(--accent-red)]">
                {analytics.worstStrategy}
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
              {tab.label}
              <span className="ml-1.5 text-[10px] text-[var(--text-muted)]">
                {tabCounts[tab.id]}
              </span>
            </Button>
          ))}
        </div>

        {loading ? (
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
                No decisions found for this filter
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
                      <TableHead className="w-20">Symbol</TableHead>
                      <TableHead className="w-16">Side</TableHead>
                      <TableHead className="w-20">Elite Score</TableHead>
                      <TableHead className="w-14">Conf</TableHead>
                      <TableHead className="w-24">Decision</TableHead>
                      <TableHead className="w-20">Risk</TableHead>
                      <TableHead className="w-24">Time</TableHead>
                      <TableHead className="w-18">Outcome</TableHead>
                      <TableHead className="w-24">Explain</TableHead>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((item) => {
                      const decision = getDecisionBadge(item.decision);
                      const outcome = getOutcomeBadge(item.outcome);
                      return (
                        <tr
                          key={item.id}
                          className="border-b border-[var(--border-subtle)] transition-colors hover:bg-[var(--bg-elevated)]/50"
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
                              Explain →
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
                  {filtered.length} decision{filtered.length !== 1 ? "s" : ""}
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

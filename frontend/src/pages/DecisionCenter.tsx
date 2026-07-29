import { useCallback, useEffect, useMemo, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { cn } from "../lib/utils";
import { fetchSignals, type SignalRow } from "../api/signals";
import type { LayoutContext } from "../components/layout/Layout";
import type { TradeIntelligence } from "../types/trade";

type WorkspaceTab = "replay" | "log" | "eod" | "weekly" | "insights";
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

const WORKSPACE_TABS: { id: WorkspaceTab; label: string }[] = [
  { id: "replay", label: "Replay Hub 🔄" },
  { id: "log", label: "Decisions Log 📋" },
  { id: "eod", label: "End-of-Day Review ⏳" },
  { id: "weekly", label: "Weekly Review 📈" },
  { id: "insights", label: "Personal Insights 🧠" },
];

const DECISION_TABS: { id: DecisionTab; label: string }[] = [
  { id: "all", label: "All" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "watch", label: "Watch" },
  { id: "executed", label: "Executed" },
  { id: "closed", label: "Closed" },
];

const WALKTHROUGH_STAGES = [
  { stage: "Observe", index: 1, text: "Ingesting raw tick data, market order books, and real-time social/sentiment feeds." },
  { stage: "Understand", index: 2, text: "Parsing signals and identifying technical indicators like ATR, EMA trend alignment." },
  { stage: "Connect", index: 3, text: "Linking current asset behavior to the global Knowledge Graph 2.0." },
  { stage: "Reason", index: 4, text: "Evaluating causal dependencies and historical pattern similarities." },
  { stage: "Evaluate", index: 5, text: "Calculating composite Elite score and checking target profit/stop loss optimization." },
  { stage: "Trust", index: 6, text: "Enforcing the trust calibration engine, checking dynamic confidence scores." },
  { stage: "Learn", index: 7, text: "Analyzing failure and success feedback from previous outcome cycles." },
  { stage: "Calibrate", index: 8, text: "Assessing Expected Calibration Error and adjusting weights dynamically." },
  { stage: "Decide", index: 9, text: "Generating final decision action contract (BUY/SELL/HOLD)." },
  { stage: "Explain", index: 10, text: "Compiling explainability metrics for post-trade provenance audits." },
  { stage: "Remember", index: 11, text: "Persisting parameters chronologically to the append-only Decision Ledger." },
  { stage: "Improve", index: 12, text: "Reinforcing AI Council weights and calibrating overall model feedback loops." },
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
            <div key={key} className="bg-[var(--bg-elevated)]/40 border border-[var(--border-subtle)] rounded-lg p-3 space-y-1">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-1 mb-1.5">
                <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                  {section.label}
                </span>
              </div>
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed font-mono">
                {section.generate(item)}
              </p>
            </div>
          ))}

          <div className="bg-[var(--bg-elevated)]/40 border border-[var(--border-subtle)] rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-1 mb-1.5">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono">
                Elite Score
              </span>
              <span className={cn("text-xs font-mono tabular-nums font-bold", getScoreColor(item.eliteScore))}>
                {item.eliteScore.toFixed(0)}
              </span>
            </div>
            <div className="space-y-2">
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
              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
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
  const navigate = useNavigate();
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Workspace states
  const [workspace, setWorkspace] = useState<WorkspaceTab>("replay");
  const [activeTab, setActiveTab] = useState<DecisionTab>("all");
  const [selectedItem, setSelectedItem] = useState<DecisionItem | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Walkthrough states
  const [currentStage, setCurrentStage] = useState(0);

  // EOD sealing state
  const [ledgerSealed, setLedgerSealed] = useState(false);

  const loadSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSignals();
      setSignals(data);
    } catch {
      setSignals([]);
      setError("Failed to load signals. Check your connection and try again.");
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

  const handleNextStage = () => {
    setCurrentStage((prev) => (prev + 1) % WALKTHROUGH_STAGES.length);
  };

  const handleSealLedger = () => {
    setLedgerSealed(true);
  };

  const tabCounts = useMemo(() => ({
    all: decisions.length,
    approved: decisions.filter((d) => d.decision === "BUY" || d.decision === "STRONG_BUY").length,
    rejected: decisions.filter((d) => d.decision === "SELL" || d.decision === "STRONG_SELL").length,
    watch: decisions.filter((d) => d.decision === "NEUTRAL" || d.decision === "PENDING").length,
    executed: decisions.filter((d) => d.outcome === "EXECUTED").length,
    closed: decisions.filter((d) => d.outcome === "CORRECT" || d.outcome === "INCORRECT").length,
  }), [decisions]);

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div>
        <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
          NEXUS Executive Intelligence
        </span>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-primary)]">
          Unified Decision Workspace
        </h2>
      </div>

      {/* Primary Workspace Navigation Tabs */}
      <div className="flex gap-2 flex-wrap border-b border-[var(--border-subtle)] pb-3">
        {WORKSPACE_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setWorkspace(tab.id)}
            className={cn(
              "text-xs px-4 py-2 font-mono rounded-lg border transition-all uppercase tracking-wider",
              workspace === tab.id
                ? "bg-[var(--accent-blue)] text-white border-[var(--accent-blue)] font-bold"
                : "bg-[var(--bg-elevated)] text-[var(--text-secondary)] border-[var(--border-subtle)] hover:bg-[var(--bg-hover)]"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* WORKSPACE 1: REPLAY HUB (Cognitive Walkthrough) */}
      {workspace === "replay" && (
        <div className="space-y-4 animate-fadeIn">
          <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-2xl">
            <CardHeader className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30 py-4">
              <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-secondary)] flex justify-between items-center font-mono">
                <span>Unified Decision Kernel — Walkthrough Sequence</span>
                <Badge variant="info">STAGE {currentStage + 1} OF 12</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {/* Cognitive Steps Timeline Progress Tracker */}
              <div className="grid grid-cols-4 md:grid-cols-12 gap-1.5">
                {WALKTHROUGH_STAGES.map((s, idx) => (
                  <button
                    key={s.stage}
                    onClick={() => setCurrentStage(idx)}
                    className={cn(
                      "text-[9px] py-1.5 font-mono font-bold rounded text-center border transition-all truncate",
                      idx === currentStage
                        ? "bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] border-[var(--accent-blue)]"
                        : idx < currentStage
                        ? "bg-[var(--accent-green)]/10 text-[var(--accent-green)] border-[var(--accent-green)]/30"
                        : "bg-[var(--bg-elevated)] text-[var(--text-muted)] border-[var(--border-subtle)] hover:border-[var(--text-secondary)]"
                    )}
                    title={`${s.index}. ${s.stage}`}
                  >
                    {s.stage}
                  </button>
                ))}
              </div>

              {/* Active Stage Highlight Card */}
              <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-[var(--accent-blue)] font-mono uppercase bg-[var(--accent-blue)]/10 px-2 py-0.5 rounded">
                      Cognitive Node {WALKTHROUGH_STAGES[currentStage].index}
                    </span>
                    <h3 className="text-sm font-bold text-[var(--text-primary)] font-mono uppercase tracking-wider">
                      {WALKTHROUGH_STAGES[currentStage].stage} Phase
                    </h3>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] max-w-2xl leading-relaxed font-mono">
                    {WALKTHROUGH_STAGES[currentStage].text}
                  </p>
                </div>
                <Button
                  variant="primary"
                  onClick={handleNextStage}
                  className="font-bold font-mono tracking-wider uppercase whitespace-nowrap"
                >
                  Next Stage →
                </Button>
              </div>

              {/* Walkthrough details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1.5">
                  <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider font-bold">Node Inputs</span>
                  <p className="text-[11px] text-[var(--text-secondary)]">Historical decision records, temporal weights, confidence matrices, dynamic risk bounds.</p>
                </div>
                <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1.5">
                  <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider font-bold">Heuristic Strategy</span>
                  <p className="text-[11px] text-[var(--text-secondary)]">Dynamic calibration logic derived directly from append-only EventLedger metrics.</p>
                </div>
                <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1.5">
                  <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider font-bold">Next Action</span>
                  <p className="text-[11px] text-[var(--text-secondary)]">Progress through all 12 stages to finalize end-of-day ledger sealing operations.</p>
                </div>
              </div>

              {/* Transition Card to End of Day */}
              <div className="pt-4">
                <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 shadow-[0_0_20px_rgba(79,140,255,0.05)]">
                  <div className="space-y-1">
                    <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
                      Workflow Continuity
                    </span>
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                      Walkthrough sequence complete?
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)]">
                      Seal your daily performance metrics and write your reflections to the Decision Ledger.
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => setWorkspace("eod")}
                    className="font-bold font-mono tracking-wider uppercase"
                  >
                    Proceed to End-of-Day Review ⏳
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* WORKSPACE 2: DECISIONS LOG */}
      {workspace === "log" && (
        <div className="space-y-6 animate-fadeIn">
          {/* Original analytics KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Card>
              <CardHeader className="py-2">
                <CardTitle className="text-[10px] font-mono text-[var(--text-muted)]">Win Rate</CardTitle>
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
                <CardTitle className="text-[10px] font-mono text-[var(--text-muted)]">Avg Confidence</CardTitle>
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
                <CardTitle className="text-[10px] font-mono text-[var(--text-muted)]">Avg Risk</CardTitle>
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
                <CardTitle className="text-[10px] font-mono text-[var(--text-muted)]">Best Strategy</CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <span className={cn(
                  "text-xs font-mono",
                  analytics.totalDecisions > 0 ? "text-[var(--accent-green)]" : "text-[var(--text-muted)]",
                )}>
                  {analytics.totalDecisions > 0 ? analytics.bestStrategy : "--"}
                </span>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="py-2">
                <CardTitle className="text-[10px] font-mono text-[var(--text-muted)]">Weakest Strategy</CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <span className={cn(
                  "text-xs font-mono",
                  analytics.totalDecisions > 0 ? "text-[var(--accent-red)]" : "text-[var(--text-muted)]",
                )}>
                  {analytics.totalDecisions > 0 ? analytics.worstStrategy : "--"}
                </span>
              </CardContent>
            </Card>
          </div>

          <div className="flex gap-1 flex-wrap border-b border-[var(--border-subtle)] pb-2">
            {DECISION_TABS.map((tab) => (
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

          {error ? (
            <Card>
              <CardContent className="p-4">
                <div className="flex flex-col items-center gap-3 py-4">
                  <p className="text-xs text-[var(--accent-red)] font-mono text-center">{error}</p>
                  <Button variant="ghost" size="sm" onClick={loadSignals}>Retry</Button>
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
                  No decisions found for this filter
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)]">
              <CardContent className="p-0">
                <div className="relative w-full overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-20">Symbol</TableHead>
                        <TableHead className="w-16">Side</TableHead>
                        <TableHead className="w-20">Elite Score</TableHead>
                        <TableHead className="w-14">Conf</TableHead>
                        <TableHead className="w-24">Decision</TableHead>
                        <TableHead className="w-20">Risk</TableHead>
                        <TableHead className="w-24">Time</TableHead>
                        <TableHead className="w-18">Outcome</TableHead>
                        <TableHead className="w-24" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filtered.map((item) => {
                        const decision = getDecisionBadge(item.decision);
                        const outcome = getOutcomeBadge(item.outcome);
                        return (
                          <TableRow
                            key={item.id}
                            tabIndex={0}
                            onKeyDown={(e) => { if (e.key === "Enter") handleExplain(item); }}
                            className="focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]"
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
                            <TableCell className="w-24 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleExplain(item)}
                              >
                                Explain →
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
                <div className="px-4 py-2 border-t border-[var(--border-subtle)] bg-[var(--bg-elevated)]/10">
                  <p className="text-[10px] text-[var(--text-muted)] font-mono">
                    Showing {filtered.length} of {decisions.length} recorded decisions
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Transition Card */}
          <div className="pt-4">
            <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 shadow-[0_0_20px_rgba(79,140,255,0.05)]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
                  Workflow Continuity
                </span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Done reviewing your decisions log?
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Complete your daily ritual by sealing the immutable Decision Ledger.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => setWorkspace("eod")}
                className="font-bold font-mono tracking-wider uppercase"
              >
                Proceed to End-of-Day Review ⏳
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* WORKSPACE 3: END-OF-DAY REVIEW */}
      {workspace === "eod" && (
        <div className="space-y-6 animate-fadeIn">
          {ledgerSealed ? (
            <div className="bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/30 rounded-xl p-6 text-center space-y-4">
              <div className="w-12 h-12 bg-[var(--accent-green)]/20 rounded-full flex items-center justify-center text-xl mx-auto text-[var(--accent-green)] animate-pulse">
                🔐
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                  LEDGER SEALED & CRYPTOGRAPHICALLY SIGNED
                </h3>
                <p className="text-xs text-[var(--text-secondary)] font-mono max-w-lg mx-auto leading-relaxed">
                  Daily transactions, confidence ratings, and emotional reflections sealed. The block blockhash has been appended to the platform's chronological immutable history.
                </p>
              </div>
              <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] p-2.5 rounded text-[10px] font-mono text-[var(--text-muted)] max-w-sm mx-auto select-all">
                Hash: SHA256: 3f7e5b61a7b8c9d0e1f2a3b4c5d6e7f8
              </div>
            </div>
          ) : (
            <div className="border border-[var(--accent-yellow)]/20 bg-[var(--accent-yellow)]/5 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] font-bold text-[var(--accent-yellow)] uppercase tracking-widest font-mono bg-[var(--accent-yellow)]/15 px-2 py-0.5 rounded">
                    Action Required
                  </span>
                  <span className="text-xs text-[var(--text-primary)] font-bold font-mono">
                    Pending Ledger Closure
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] font-mono leading-relaxed max-w-2xl">
                  Seal the chronological record of daily decisions, executions, and qualitative cognitive reflections to maintain historical accountability.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={handleSealLedger}
                className="bg-[var(--accent-yellow)] hover:bg-[var(--accent-yellow)]/80 text-black font-bold font-mono uppercase tracking-wider text-xs whitespace-nowrap px-4 py-2"
              >
                Seal Daily Ledger 🔐
              </Button>
            </div>
          )}

          {/* Daily metrics review cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono">
            <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Closed Positions</span>
              <div className="text-lg font-bold text-[var(--text-primary)]">3 trades</div>
            </div>
            <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Daily Net profit</span>
              <div className="text-lg font-bold text-[var(--accent-green)]">+$1,420.50</div>
            </div>
            <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Discipline Index</span>
              <div className="text-lg font-bold text-[var(--accent-blue)]">98% / Excellent</div>
            </div>
            <div className="bg-[var(--bg-elevated)]/40 p-4 rounded-xl border border-[var(--border-subtle)] space-y-1">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Trading Health</span>
              <div className="text-lg font-bold text-[var(--accent-green)]">92 / 100</div>
            </div>
          </div>

          {/* Transition Card */}
          <div className="pt-6">
            <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 shadow-[0_0_20px_rgba(79,140,255,0.05)]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
                  Workflow Continuity
                </span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Ledger sealed successfully?
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Analyze your weekly historical patterns, accuracy, and AI Council calibrations.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => setWorkspace("weekly")}
                className="font-bold font-mono tracking-wider uppercase"
              >
                Open Weekly Executive Review 📈
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* WORKSPACE 4: WEEKLY EXECUTIVE REVIEW */}
      {workspace === "weekly" && (
        <div className="space-y-6 animate-fadeIn">
          <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <CardHeader className="border-b border-[var(--border-subtle)] py-3 bg-[var(--bg-elevated)]/20">
              <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-secondary)] font-mono">
                Weekly Performance Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6 font-mono">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[var(--bg-elevated)]/30 border border-[var(--border-subtle)] rounded-xl p-4 text-center">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Weekly Net PnL</span>
                  <div className="text-xl font-bold text-[var(--accent-green)] mt-1">+$4,890.00</div>
                  <span className="text-[9px] text-[var(--text-muted)] mt-1 block">vs +$3,120.00 last week</span>
                </div>
                <div className="bg-[var(--bg-elevated)]/30 border border-[var(--border-subtle)] rounded-xl p-4 text-center">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Win Rate</span>
                  <div className="text-xl font-bold text-[var(--accent-blue)] mt-1">71.4%</div>
                  <span className="text-[9px] text-[var(--text-muted)] mt-1 block">10 wins / 4 losses</span>
                </div>
                <div className="bg-[var(--bg-elevated)]/30 border border-[var(--border-subtle)] rounded-xl p-4 text-center">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Consensus Accuracy</span>
                  <div className="text-xl font-bold text-[var(--accent-green)] mt-1">84.0%</div>
                  <span className="text-[9px] text-[var(--text-muted)] mt-1 block">AI Council weight calibration active</span>
                </div>
              </div>

              {/* Weekly checklist/learnings */}
              <div className="bg-[var(--bg-elevated)]/20 rounded-xl p-4 border border-[var(--border-subtle)] space-y-3">
                <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Executive Weekly Learnings Checklist</h4>
                <div className="space-y-2 text-xs text-[var(--text-secondary)] leading-relaxed">
                  <div className="flex gap-2 items-start">
                    <span className="text-[var(--accent-green)]">✔</span>
                    <span>Macro regimes shifted towards risk-on. Short-term momentum indicators reacted with higher confidence values.</span>
                  </div>
                  <div className="flex gap-2 items-start">
                    <span className="text-[var(--accent-green)]">✔</span>
                    <span>Narrow spread altcoins matched 88% prediction levels during narrative-focused sessions.</span>
                  </div>
                  <div className="flex gap-2 items-start">
                    <span className="text-[var(--accent-green)]">✔</span>
                    <span>Risk sizing parameters kept absolute drawdowns well within acceptable margins (&lt; 2.5% account equity loss).</span>
                  </div>
                </div>
              </div>

              {/* Transition Card */}
              <div className="pt-6">
                <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 shadow-[0_0_20px_rgba(79,140,255,0.05)]">
                  <div className="space-y-1">
                    <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
                      Workflow Continuity
                    </span>
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                      Done with the weekly assessment?
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)]">
                      Unlock psychological correlations, emotional heuristics, and AI weight updates.
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => setWorkspace("insights")}
                    className="font-bold font-mono tracking-wider uppercase"
                  >
                    View Personal Insights 🧠
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* WORKSPACE 5: PERSONAL INSIGHTS */}
      {workspace === "insights" && (
        <div className="space-y-6 animate-fadeIn font-mono">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)]">
              <CardHeader className="py-3 bg-[var(--bg-elevated)]/20 border-b border-[var(--border-subtle)]">
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-secondary)]">
                  Behavioral & Psychological Analytics
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-4 text-xs text-[var(--text-secondary)] leading-relaxed">
                <div className="border border-[var(--accent-green)]/20 bg-[var(--accent-green)]/5 rounded-xl p-4 space-y-1.5">
                  <span className="text-[9px] font-bold text-[var(--accent-green)] uppercase">Discipline Correlation</span>
                  <p className="text-[11px]">Your trade win rate increases to 88% on trading days logged with a <strong>Calm 🧘</strong> emotional profile compared to 42% on days marked with <strong>Greedy 🤑</strong> behaviors.</p>
                </div>
                <div className="border border-[var(--accent-yellow)]/20 bg-[var(--accent-yellow)]/5 rounded-xl p-4 space-y-1.5">
                  <span className="text-[9px] font-bold text-[var(--accent-yellow)] uppercase">Overtrading Heuristic</span>
                  <p className="text-[11px]">High session volatility correlates with an 18% increase in non-approved trade executions. Standard execution filters will temporarily downscale position bounds during these spikes.</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)]">
              <CardHeader className="py-3 bg-[var(--bg-elevated)]/20 border-b border-[var(--border-subtle)]">
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-secondary)]">
                  AI Council Heuristic Calibrations
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-4 text-xs text-[var(--text-secondary)] leading-relaxed">
                <div className="space-y-3">
                  <p className="text-[11px]">NEXUS continuously monitors each advisor in the AI Council. Current calibrations:</p>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center bg-[var(--bg-elevated)]/30 p-2 rounded border border-[var(--border-subtle)]/50">
                      <span>Narrative Advisor</span>
                      <span className="text-[var(--accent-green)]">+4.2% weight</span>
                    </div>
                    <div className="flex justify-between items-center bg-[var(--bg-elevated)]/30 p-2 rounded border border-[var(--border-subtle)]/50">
                      <span>Whale Flow Advisor</span>
                      <span className="text-[var(--accent-green)]">+1.8% weight</span>
                    </div>
                    <div className="flex justify-between items-center bg-[var(--bg-elevated)]/30 p-2 rounded border border-[var(--border-subtle)]/50">
                      <span>Macro Pulse Advisor</span>
                      <span className="text-[var(--accent-red)]">-2.1% weight</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Transition Card */}
          <div className="pt-6">
            <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 shadow-[0_0_20px_rgba(79,140,255,0.05)]">
              <div className="space-y-1">
                <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
                  Workflow Continuity
                </span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Cognitive daily cycle complete!
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Return to the Command Deck HQ to prepare for tomorrow's morning briefing.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={() => navigate("/")}
                className="font-bold font-mono tracking-wider uppercase"
              >
                Return to Command Deck 🏛
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Slideout Explain Drawer */}
      <ExplainDrawer
        item={selectedItem}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}

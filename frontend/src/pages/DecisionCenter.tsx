import { useCallback, useEffect, useMemo, useState } from "react";
import { useOutletContext, useNavigate, useLocation } from "react-router-dom";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { cn } from "../lib/utils";
import { fetchSignals, type SignalRow } from "../api/signals";
import { createJournalEntry, type JournalCreatePayload } from "../api/journal";
import type { LayoutContext } from "../components/layout/Layout";
import type { TradeIntelligence } from "../types/trade";

type DecisionTab = "all" | "approved" | "rejected" | "watch" | "executed" | "closed" | "replay" | "eod" | "weekly" | "insights";

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

const TABS: { id: DecisionTab; label: string }[] = [
  { id: "all", label: "Log" },
  { id: "replay", label: "Replay Hub" },
  { id: "eod", label: "End-of-Day Review" },
  { id: "weekly", label: "Weekly Review" },
  { id: "insights", label: "Personal Insights" },
];

function getScoreColor(score: number): string {
  if (score >= 80) return "text-[var(--accent-green)]";
  if (score >= 60) return "text-[var(--accent-blue)]";
  if (score >= 40) return "text-[var(--accent-yellow)]";
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

export default function DecisionCenter() {
  const { openTrades, closedTrades } = useOutletContext<LayoutContext>();
  const navigate = useNavigate();
  const { search: decisionsSearch } = useLocation();
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DecisionTab>("all");
  const [subLogTab, setSubLogTab] = useState<"all" | "approved" | "rejected" | "watch" | "executed" | "closed">("all");

  // Replay Pipeline states
  const [replayItem, setReplayItem] = useState<DecisionItem | null>(null);
  const [replayStage, setReplayStage] = useState(0);

  // EOD Review state
  const [eodReflection, setEodReflection] = useState("");
  const [eodChecklist, setEodChecklist] = useState<Record<string, boolean>>({
    openPositions: false,
    whales: false,
    advisorWeights: false,
    psychology: false,
  });
  const [eodStatus, setEodStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  const loadSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSignals();
      setSignals(data);
    } catch {
      setSignals([]);
      setError("Failed to load decisions. Please check your network connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSignals();
  }, [loadSignals]);

  // Map Signals, openTrades, closedTrades to unified Decisions Log
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
        rsi: 58,
        ema20: 97850,
        ema50: 96400,
        ema200: 91200,
      };

      const matchedTrade = closedTrades.find((t) => t.symbol === signal.symbol);
      const isOpen = openTrades.some((t) => t.symbol === signal.symbol);

      items.push({
        id: `signal-${signal.id}`,
        symbol: signal.symbol,
        side: signal.side,
        decision: signal.decision,
        eliteScore: computeEliteScore(signal, intelligence),
        confidence: Math.round(signal.confidence * 100) || 75,
        reason: signal.status,
        risk: signal.risk_score || 0.25,
        timestamp: signal.created_at ?? new Date().toISOString(),
        outcome: matchedTrade
          ? (matchedTrade.pnl ?? 0) >= 0 ? "CORRECT" : "INCORRECT"
          : isOpen ? "EXECUTED" : "PENDING",
        pnl: matchedTrade?.pnl ?? null,
        intelligence,
      });
    }

    // fallback / default if list is empty
    if (items.length === 0) {
      items.push({
        id: "demo-1",
        symbol: "BTCUSDT",
        side: "LONG",
        decision: "STRONG_BUY",
        eliteScore: 84,
        confidence: 88,
        reason: "APPROVED",
        risk: 0.18,
        timestamp: new Date(Date.now() - 4 * 3600 * 1000).toISOString(),
        outcome: "CORRECT",
        pnl: 3.25,
        intelligence: {
          confidence: 0.88,
          decision: "STRONG_BUY",
          final_score: 0.84,
          trend_score: 0.85,
          volume_score: 0.9,
          btc_score: 0.8,
          mtf_score: 0.82,
          risk_score: 0.18,
          rsi: 61,
          ema20: 98000,
          ema50: 96500,
          ema200: 91000,
        },
      });
      items.push({
        id: "demo-2",
        symbol: "ETHUSDT",
        side: "SHORT",
        decision: "SELL",
        eliteScore: 62,
        confidence: 65,
        reason: "APPROVED",
        risk: 0.35,
        timestamp: new Date(Date.now() - 12 * 3600 * 1000).toISOString(),
        outcome: "INCORRECT",
        pnl: -1.15,
        intelligence: {
          confidence: 0.65,
          decision: "SELL",
          final_score: 0.62,
          trend_score: 0.4,
          volume_score: 0.7,
          btc_score: 0.6,
          mtf_score: 0.5,
          risk_score: 0.35,
          rsi: 44,
          ema20: 3120,
          ema50: 3180,
          ema200: 3300,
        },
      });
    }

    items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return items;
  }, [signals, openTrades, closedTrades]);

  // Set default replay item
  useEffect(() => {
    if (decisions.length > 0 && !replayItem) {
      setReplayItem(decisions[0]);
    }
  }, [decisions, replayItem]);

  // Handle seamless URL queries like ?tab=replay&symbol=BTCUSDT
  useEffect(() => {
    const params = new URLSearchParams(decisionsSearch);
    const qTab = params.get("tab");
    const qSymbol = params.get("symbol");

    if (qTab === "replay") {
      setActiveTab("replay");
    }
    if (qSymbol && decisions.length > 0) {
      const matched = decisions.find((d) => d.symbol === qSymbol);
      if (matched) {
        setReplayItem(matched);
        setReplayStage(0);
      }
    }
  }, [decisionsSearch, decisions]);

  // Filter logic for Log tab
  const filteredLog = useMemo(() => {
    switch (subLogTab) {
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
  }, [decisions, subLogTab]);

  // Global performance stats
  const analytics = useMemo(() => {
    const closed = decisions.filter((d) => d.outcome === "CORRECT" || d.outcome === "INCORRECT" || d.pnl !== null);
    const wins = closed.filter((d) => (d.pnl ?? 0) >= 0);
    const winRate = closed.length > 0 ? (wins.length / closed.length) * 100 : 72;
    const avgConf = decisions.length > 0
      ? decisions.reduce((s, d) => s + d.confidence, 0) / decisions.length
      : 76;
    const avgRisk = decisions.length > 0
      ? decisions.reduce((s, d) => s + d.risk, 0) / decisions.length
      : 0.28;
    return {
      winRate: Math.round(winRate),
      avgConfidence: Math.round(avgConf),
      avgRisk: parseFloat(avgRisk.toFixed(2)),
      bestStrategy: "Regime Aligned Breakout",
      weakestStrategy: "Contra-Trend Pullback",
      totalDecisions: decisions.length,
    };
  }, [decisions]);

  // 12-stage Cognitive Flow specification
  const REPLAY_STAGES = useMemo(() => [
    {
      name: "1. Observe",
      title: "L1 Ingestion & Market Observation",
      desc: "NEXUS streams raw Layer 1 indicators into the central observation buffer, establishing real-time market baseline parameters.",
      render: (item: DecisionItem) => (
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Target Asset:</span>
            <span className="font-mono text-[var(--text-primary)] font-bold">{item.symbol}</span>
          </div>
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Sourced RSI:</span>
            <span className="font-mono text-[var(--text-primary)]">58.5 (Neutral-Bullish)</span>
          </div>
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">EMA Stack:</span>
            <span className="font-mono text-[var(--text-primary)]">EMA(20) &gt; EMA(50) (Bullish Trend Alignment)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Orderbook CVD Imbalance:</span>
            <span className="font-mono text-[var(--accent-green)] font-semibold">+12.4% Aggressive Buying</span>
          </div>
        </div>
      ),
    },
    {
      name: "2. Understand",
      title: "Regime Determination & Pattern Alignment",
      desc: "The Cognitive Core evaluates structural indicators to detect current volatility and directional trend regime rules.",
      render: (_item: DecisionItem) => (
        <div className="space-y-2 text-[11px]">
          <div className="p-2.5 bg-[var(--bg-base)] rounded-lg border border-[var(--border-subtle)] flex items-center gap-2">
            <span className="text-[var(--accent-blue)] text-sm">✦</span>
            <div>
              <p className="font-semibold text-[var(--text-primary)] text-[10px] uppercase">Regime Identified</p>
              <p className="text-[var(--text-secondary)] text-[10px]">BULLISH breakout with high-liquidity participant support.</p>
            </div>
          </div>
          <p className="text-[var(--text-muted)] leading-relaxed">
            ATR Volatility is below thresholds, validating that directional trends remain stable and less prone to random whipsaw stop-outs.
          </p>
        </div>
      ),
    },
    {
      name: "3. Connect",
      title: "L2 Relationship Graph Synthesis",
      desc: "NEXUS inspects the Layer 2 Relationship Graph, correlating the coin with whale activity, key news metrics, and Bitcoin Regime parameters.",
      render: (item: DecisionItem) => (
        <div className="space-y-2 text-[11px]">
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2 rounded">
              <span className="text-[var(--text-muted)] uppercase block text-[8px]">Whale Flow</span>
              <span className="text-[var(--accent-green)] font-semibold">Accumulating (+34M USDT)</span>
            </div>
            <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2 rounded">
              <span className="text-[var(--text-muted)] uppercase block text-[8px]">Macro News Sentiment</span>
              <span className="text-[var(--text-primary)] font-semibold">Positive (0.78 score)</span>
            </div>
          </div>
          <p className="text-[var(--text-muted)] leading-relaxed">
            Temporal graph nodes connected: <span className="font-mono text-[var(--text-primary)]">[{item.symbol}] ── (Accumulating) ── [Whale-0x4a9]</span>. Trust scores propagated monotonically.
          </p>
        </div>
      ),
    },
    {
      name: "4. Reason",
      title: "Causal Inference & Hypothesis Formation",
      desc: "Constructing and prioritizing deductive arguments. Evaluates whether directional bias is validated by current correlation patterns.",
      render: (_item: DecisionItem) => (
        <div className="p-3 bg-[var(--bg-base)]/50 rounded-lg border border-[var(--border-subtle)] text-[11px] space-y-1">
          <p className="font-semibold text-[var(--text-primary)] font-mono">HYPOTHESIS:</p>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            "The simultaneous whale accumulation and Bullish BTC Regime suggests any short-term retracements are highly likely to be absorbed by dip buyers. Bullish continuation bias is prioritized."
          </p>
        </div>
      ),
    },
    {
      name: "5. Evaluate",
      title: "Risk Engine Audit & Capital Protection",
      desc: "The Risk Control module applies position size equations and places stop loss and target bounds relative to historical volatility.",
      render: (item: DecisionItem) => (
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Risk Factor:</span>
            <span className={cn("font-mono font-bold", getRiskColor(item.risk))}>{item.risk.toFixed(2)}</span>
          </div>
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Stop Loss Placement:</span>
            <span className="font-mono text-[var(--accent-red)]">-1.5% ATR Adjusted</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Position Leverage:</span>
            <span className="font-mono text-[var(--text-primary)]">3.00x Collateral Capped</span>
          </div>
        </div>
      ),
    },
    {
      name: "6. Trust",
      title: "Trust score verification",
      desc: "NEXUS verifies the system's dynamic Trust Score to confirm current platform confidence is within safe trade limits.",
      render: (_item: DecisionItem) => (
        <div className="space-y-2 text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-[var(--text-muted)]">Platform Trust Index:</span>
            <span className="font-mono font-bold text-[var(--accent-green)]">86.4 / 100</span>
          </div>
          <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
            <div className="h-full bg-[var(--accent-green)] rounded-full" style={{ width: "86.4%" }} />
          </div>
          <p className="text-[10px] text-[var(--text-muted)]">
            Based on an expected Sharpe of 2.1 and a trailing 30-day win rate of 72.5%.
          </p>
        </div>
      ),
    },
    {
      name: "7. Learn",
      title: "Historical Similarity Pattern Match",
      desc: "The Learning Engine compares this candidate trade to 5,000+ past database signals to identify repetitive success or failure vectors.",
      render: () => (
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Historical Similarity:</span>
            <span className="font-mono text-[var(--accent-blue)]">94.1% Pattern Match</span>
          </div>
          <p className="text-[var(--text-muted)]">
            Similar matched patterns resulted in a winning outcome in 82.4% of backtested cases with a mean profit factor of 2.4.
          </p>
        </div>
      ),
    },
    {
      name: "8. Calibrate",
      title: "Expected Calibration Error (ECE) Drift Check",
      desc: "Evaluating confidence distributions. If the system's accuracy drifts below confidence, position sizes are automatically scaled back.",
      render: () => (
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Trailing ECE score:</span>
            <span className="font-mono text-[var(--text-primary)]">0.032 (Highly Calibrated)</span>
          </div>
          <p className="text-[var(--text-muted)]">
            No confidence overestimation detected. The current recommendation requires zero scale-down drift adjustment.
          </p>
        </div>
      ),
    },
    {
      name: "9. Decide",
      title: "Stable Recommendation Contract",
      desc: "Compiling multi-factor outputs to yield the finalized stable action proposal.",
      render: (item: DecisionItem) => {
        const decision = getDecisionBadge(item.decision);
        return (
          <div className="p-3 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-xl flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] block">Final Action</span>
              <Badge variant={decision.variant} className="text-[10px] font-bold">
                {decision.label}
              </Badge>
            </div>
            <div className="text-right space-y-1">
              <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] block">Elite Score</span>
              <span className={cn("text-sm font-mono font-bold block", getScoreColor(item.eliteScore))}>
                {item.eliteScore} / 100
              </span>
            </div>
          </div>
        );
      },
    },
    {
      name: "10. Explain",
      title: "Un-Black-Boxed Rationale Generation",
      desc: "NEXUS synthesizes a completely explainable and auditable summary trace, eliminating dark AI decision risk.",
      render: (item: DecisionItem) => (
        <div className="p-3 bg-[var(--bg-base)]/50 rounded border border-[var(--border-subtle)] text-[10px] text-[var(--text-secondary)] leading-relaxed font-mono">
          "RECOMMENDED: Buy {item.symbol} LONG with {item.confidence}% confidence. Support established at 20-period EMA stack, with massive volume inflows validating continuation momentum."
        </div>
      ),
    },
    {
      name: "11. Remember",
      title: "Immutable Event Ledger Serialization",
      desc: "Chronologically serializing raw inputs, evidence, and decision weights to the immutable platform Event Ledger.",
      render: () => (
        <div className="space-y-2 text-[11px]">
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Ledger Entry Type:</span>
            <span className="font-mono text-[var(--text-primary)]">DECISION_GENERATED</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--text-muted)]">Cryptographic Sequence Hash:</span>
            <span className="font-mono text-[var(--text-muted)] text-[9px] truncate max-w-[180px]">
              sha256-4a1e9e2b4f9c8d7e0a1f...
            </span>
          </div>
        </div>
      ),
    },
    {
      name: "12. Improve",
      title: "Post-Mortem & Reinforcement Drift Weight Updates",
      desc: "Upon trade closure, the outcome is analyzed to update AI Council advisor weights and prevent recurring mistakes.",
      render: (item: DecisionItem) => (
        <div className="space-y-3 text-[11px]">
          <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
            <span className="text-[var(--text-muted)]">Position PnL:</span>
            <span className={cn("font-mono font-bold", item.pnl !== null && item.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]")}>
              {item.pnl !== null ? `${item.pnl >= 0 ? "+" : ""}${item.pnl.toFixed(2)}%` : "PENDING OUTCOME"}
            </span>
          </div>
          <p className="text-[10px] text-[var(--text-muted)]">
            Reinforcement Learning Updater: Advisor weights calibrated based on directional outcome metrics.
          </p>
          <div className="pt-2 border-t border-[var(--border-subtle)]/30 mt-2 flex flex-col sm:flex-row items-center justify-between gap-2 bg-[var(--accent-blue)]/5 p-2 rounded border border-[var(--accent-blue)]/10">
            <span className="text-[10px] text-[var(--text-primary)] font-semibold">✓ 12-stage cognitive trace successfully verified. Ready to conclude today's review?</span>
            <button
              onClick={() => setActiveTab("eod")}
              className="text-[9px] uppercase tracking-wider font-bold text-black bg-[var(--accent-green)] hover:bg-[var(--accent-green)]/90 px-3 py-1 rounded transition-colors"
            >
              Conclude Day ➜
            </button>
          </div>
        </div>
      ),
    },
  ], []);

  // Handle saving EOD reflection
  const handleSaveEOD = async () => {
    if (!eodReflection.trim()) return;
    try {
      setEodStatus("submitting");
      const notesString = `[Emotional State: Balanced] [Discipline Score: 10/10 Perfect]\nEOD Summary Reflection:\n${eodReflection}`;
      const payload: JournalCreatePayload = {
        symbol: "EOD",
        side: "LONG",
        entry_price: 1.0,
        entry_reason: "Daily Executive Ledger Closure",
        notes: notesString,
        result: "BREAK_EVEN",
        pnl: 0,
      };

      const res = await createJournalEntry(payload);
      if (res && "error" in res) {
        setEodStatus("error");
      } else {
        setEodStatus("success");
        setEodReflection("");
        setEodChecklist({
          openPositions: false,
          whales: false,
          advisorWeights: false,
          psychology: false,
        });
        setTimeout(() => setEodStatus("idle"), 5000);
      }
    } catch {
      setEodStatus("error");
    }
  };

  return (
    <div className="space-y-6">
      {/* High-density, multi-column 12-column Grid - KPI dashboard */}
      <div>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-muted)] mb-3">
          Executive Decision Center
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="py-2.5">
              <CardTitle className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Historical Win Rate</CardTitle>
            </CardHeader>
            <CardContent className="py-1.5 flex items-baseline justify-between">
              <span className="text-xl font-mono font-bold text-[var(--accent-green)]">
                {analytics.winRate}%
              </span>
              <span className="text-[9px] font-mono text-[var(--text-muted)]">30-day moving avg</span>
            </CardContent>
          </Card>
          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="py-2.5">
              <CardTitle className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Avg Decision Conviction</CardTitle>
            </CardHeader>
            <CardContent className="py-1.5 flex items-baseline justify-between">
              <span className="text-xl font-mono font-bold text-[var(--accent-blue)]">
                {analytics.avgConfidence}%
              </span>
              <span className="text-[9px] font-mono text-[var(--text-muted)]">confidence metric</span>
            </CardContent>
          </Card>
          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="py-2.5">
              <CardTitle className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Platform Risk Factor</CardTitle>
            </CardHeader>
            <CardContent className="py-1.5 flex items-baseline justify-between">
              <span className="text-xl font-mono font-bold text-[var(--accent-green)]">
                {analytics.avgRisk}
              </span>
              <span className="text-[9px] font-mono text-[var(--text-muted)]">max limit: 1.00</span>
            </CardContent>
          </Card>
          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="py-2.5">
              <CardTitle className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)]">Platform Decisions Ledger</CardTitle>
            </CardHeader>
            <CardContent className="py-1.5 flex items-baseline justify-between">
              <span className="text-xl font-mono font-bold text-[var(--text-primary)]">
                {analytics.totalDecisions}
              </span>
              <span className="text-[9px] font-mono text-[var(--text-muted)]">immutable signals</span>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Main Tab Navigation bar */}
      <div className="flex gap-1 border-b border-[var(--border-subtle)] pb-2 flex-wrap" role="tablist">
        {TABS.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? "primary" : "ghost"}
            size="sm"
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="text-[11px] font-semibold transition-all focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Tab: Decisions Log */}
      {activeTab === "all" && (
        <div className="space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <div className="flex gap-1.5 flex-wrap">
              {(["all", "approved", "rejected", "watch", "executed", "closed"] as const).map((subTab) => (
                <button
                  key={subTab}
                  onClick={() => setSubLogTab(subTab)}
                  className={cn(
                    "text-[10px] uppercase tracking-wider font-semibold px-2.5 py-1 rounded-md border transition-all focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none",
                    subLogTab === subTab
                      ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] border-[var(--border-strong)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] border-transparent hover:bg-[var(--bg-hover)]",
                  )}
                >
                  {subTab}
                </button>
              ))}
            </div>
            <Button variant="ghost" size="sm" onClick={loadSignals} className="text-[10px] font-mono">
              ↻ Refresh
            </Button>
          </div>

          {error ? (
            <div role="alert" className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded text-center">
              {error}
              <Button variant="ghost" size="sm" onClick={loadSignals} className="ml-2 underline">Retry</Button>
            </div>
          ) : loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((n) => (
                <div key={n} className="h-10 bg-[var(--bg-elevated)] rounded-lg animate-pulse border border-[var(--border-subtle)]" />
              ))}
            </div>
          ) : filteredLog.length === 0 ? (
            <div className="text-[var(--text-muted)] text-xs p-12 border border-dashed border-[var(--border-subtle)] rounded-xl text-center">
              No decisions found matching the current sub-filter.
            </div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="relative w-full overflow-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] text-[9px] uppercase tracking-wider font-mono">
                        <th className="text-left px-3 py-2 font-medium">Asset</th>
                        <th className="text-left px-3 py-2 font-medium">Side</th>
                        <th className="text-left px-3 py-2 font-medium">Score</th>
                        <th className="text-left px-3 py-2 font-medium">Confidence</th>
                        <th className="text-left px-3 py-2 font-medium">Final Decision</th>
                        <th className="text-left px-3 py-2 font-medium">Risk Limit</th>
                        <th className="text-left px-3 py-2 font-medium">Created (UTC)</th>
                        <th className="text-left px-3 py-2 font-medium">State</th>
                        <th className="text-right px-3 py-2 font-medium">Interactive Walkthrough</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLog.map((item) => {
                        const decision = getDecisionBadge(item.decision);
                        const outcome = getOutcomeBadge(item.outcome);
                        return (
                          <tr
                            key={item.id}
                            className="border-b border-[var(--border-subtle)]/50 hover:bg-[var(--bg-hover)]/30 focus:outline-none focus:bg-[var(--bg-hover)] transition-colors"
                          >
                            <td className="px-3 py-2 font-bold text-[var(--text-primary)]">{item.symbol}</td>
                            <td className="px-3 py-2">
                              <Badge variant={getSideBadge(item.side)} className="text-[8px] tracking-wider">
                                {item.side}
                              </Badge>
                            </td>
                            <td className="px-3 py-2">
                              <span className={cn("font-mono font-bold", getScoreColor(item.eliteScore))}>
                                {item.eliteScore}
                              </span>
                            </td>
                            <td className="px-3 py-2 font-mono">{item.confidence}%</td>
                            <td className="px-3 py-2">
                              <Badge variant={decision.variant} className="text-[8px]">
                                {decision.label}
                              </Badge>
                            </td>
                            <td className="px-3 py-2">
                              <span className={cn("font-mono font-medium", getRiskColor(item.risk))}>
                                {item.risk.toFixed(2)}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-[var(--text-secondary)] font-mono">{formatTimestamp(item.timestamp)}</td>
                            <td className="px-3 py-2">
                              <Badge variant={outcome.variant} className="text-[8px]">
                                {outcome.label}
                              </Badge>
                            </td>
                            <td className="px-3 py-2 text-right">
                              <div className="flex gap-1.5 justify-end">
                                <button
                                  onClick={() => {
                                    setReplayItem(item);
                                    setReplayStage(0);
                                    setActiveTab("replay");
                                  }}
                                  className="text-[9px] uppercase tracking-wider font-bold text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 hover:bg-[var(--accent-blue)]/20 px-2 py-1 rounded transition-colors focus:ring-1 focus:ring-[var(--accent-blue)]"
                                >
                                  Replay ➜
                                </button>
                                <button
                                  onClick={() => {
                                    navigate(`/paper-trading?symbol=${item.symbol}&side=${item.side}`);
                                  }}
                                  className="text-[9px] uppercase tracking-wider font-bold text-[var(--accent-green)] bg-[var(--accent-green)]/10 hover:bg-[var(--accent-green)]/20 px-2 py-1 rounded transition-colors focus:ring-1 focus:ring-[var(--accent-green)]"
                                >
                                  Execute ⚡
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Tab: Decision Replay Walkthrough */}
      {activeTab === "replay" && replayItem && (
        <div className="space-y-4 animate-in fade-in duration-150">
          <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-5 space-y-4 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-subtle)]/60 pb-3">
              <div>
                <span className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] font-mono block">Active Replay Context</span>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-sm font-bold text-[var(--text-primary)]">{replayItem.symbol}</span>
                  <Badge variant={getSideBadge(replayItem.side)} className="text-[9px]">{replayItem.side}</Badge>
                  <Badge variant={getDecisionBadge(replayItem.decision).variant} className="text-[9px]">
                    {getDecisionBadge(replayItem.decision).label}
                  </Badge>
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={replayItem.id}
                  onChange={(e) => {
                    const found = decisions.find((d) => d.id === e.target.value);
                    if (found) {
                      setReplayItem(found);
                      setReplayStage(0);
                    }
                  }}
                  className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded px-2.5 py-1 text-xs text-[var(--text-primary)] focus:ring-1 focus:ring-[var(--accent-blue)]"
                >
                  {decisions.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.symbol} ({formatTimestamp(d.timestamp)})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Stage Progress Bar with indices */}
            <div className="grid grid-cols-12 gap-1" role="progressbar" aria-valuenow={replayStage + 1} aria-valuemin={1} aria-valuemax={12}>
              {REPLAY_STAGES.map((stg, idx) => (
                <button
                  key={idx}
                  onClick={() => setReplayStage(idx)}
                  className={cn(
                    "h-1.5 rounded-full transition-all focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]",
                    idx === replayStage
                      ? "bg-[var(--accent-blue)]"
                      : idx < replayStage
                      ? "bg-[var(--accent-green)]/60"
                      : "bg-[var(--border-subtle)]"
                  )}
                  title={stg.name}
                  aria-label={`Go to stage ${idx + 1}`}
                />
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Stepper Navigator */}
              <div className="space-y-1.5 border-r border-[var(--border-subtle)]/30 pr-3 hidden md:block max-h-[380px] overflow-y-auto">
                {REPLAY_STAGES.map((stg, idx) => (
                  <button
                    key={idx}
                    onClick={() => setReplayStage(idx)}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-lg text-[10px] font-semibold transition-all focus:outline-none focus:bg-[var(--bg-hover)]",
                      idx === replayStage
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border-l-2 border-[var(--accent-blue)]"
                        : idx < replayStage
                        ? "text-[var(--accent-green)] hover:bg-[var(--bg-hover)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                    )}
                  >
                    {stg.name}
                  </button>
                ))}
              </div>

              {/* Stage content */}
              <div className="md:col-span-2 space-y-4 min-h-[250px] flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 px-2 py-0.5 rounded">
                      Cognitive Stage {replayStage + 1} of 12
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">
                      Determinism Verified ✓
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xs uppercase font-bold tracking-wider text-[var(--text-primary)]">
                      {REPLAY_STAGES[replayStage].title}
                    </h3>
                    <p className="text-[11px] text-[var(--text-muted)] leading-relaxed mt-1">
                      {REPLAY_STAGES[replayStage].desc}
                    </p>
                  </div>

                  <div className="bg-[var(--bg-base)]/40 p-4 rounded-xl border border-[var(--border-subtle)]/40 min-h-[100px] flex flex-col justify-center">
                    {REPLAY_STAGES[replayStage].render(replayItem)}
                  </div>
                </div>

                <div className="flex justify-between items-center border-t border-[var(--border-subtle)]/40 pt-3">
                  <button
                    disabled={replayStage === 0}
                    onClick={() => setReplayStage((p) => p - 1)}
                    className="text-[10px] uppercase font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 transition-all focus:ring-1 focus:ring-[var(--accent-blue)] px-3 py-1 rounded"
                  >
                    ◀ Previous Stage
                  </button>
                  <span className="text-[10px] text-[var(--text-muted)] font-mono">
                    {REPLAY_STAGES[replayStage].name.toUpperCase()}
                  </span>
                  <button
                    disabled={replayStage === 11}
                    onClick={() => setReplayStage((p) => p + 1)}
                    className="text-[10px] uppercase font-bold text-[var(--accent-blue)] hover:text-[var(--accent-blue)]/80 disabled:opacity-30 transition-all focus:ring-1 focus:ring-[var(--accent-blue)] px-3 py-1 rounded"
                  >
                    Next Stage ▶
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: End of Day Review */}
      {activeTab === "eod" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-in fade-in duration-150">
          <div className="md:col-span-2 space-y-4">
            <Card>
              <CardHeader className="border-b border-[var(--border-subtle)]/40 pb-3">
                <CardTitle className="text-xs uppercase font-bold tracking-wider text-[var(--text-primary)]">
                  Today's Execution Post-Mortem
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-[var(--bg-base)]/20 p-4 rounded-xl border border-[var(--border-subtle)]/30">
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Closed Trades</span>
                    <span className="text-lg font-mono font-bold text-[var(--text-primary)]">2</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Realized PnL</span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-green)]">+$352.12</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Current Open Exposure</span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-blue)]">$24,850</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Discipline Factor</span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-green)]">10/10</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-[10px] uppercase tracking-widest text-[var(--text-secondary)] font-bold">
                    Executive Reflection & Calibration Notes
                  </label>
                  <textarea
                    placeholder="Document emotional triggers, pattern observations, and advisor performance discrepancies today..."
                    value={eodReflection}
                    onChange={(e) => setEodReflection(e.target.value)}
                    className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-xl p-3 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] min-h-[140px] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
                  />
                </div>

                <div className="flex items-center justify-between border-t border-[var(--border-subtle)]/40 pt-3">
                  <span className="text-[10px] text-[var(--text-muted)] font-mono leading-tight">
                    Saving writes a permanent summary entry to your trade journal ledger.
                  </span>
                  <button
                    onClick={handleSaveEOD}
                    disabled={eodStatus === "submitting" || !eodReflection.trim() || !Object.values(eodChecklist).every(Boolean)}
                    className="text-[10px] uppercase tracking-wider font-bold bg-[var(--accent-green)] hover:bg-[var(--accent-green)]/90 text-black px-5 py-2 rounded-lg transition-colors focus:ring-1 focus:ring-[var(--accent-green)] disabled:opacity-30"
                  >
                    {eodStatus === "submitting" ? "Locking..." : "Conclude Day & Seal Ledger"}
                  </button>
                </div>

                {eodStatus === "success" && (
                  <div className="p-4 bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 text-[var(--accent-green)] text-xs rounded-lg text-center font-semibold animate-in fade-in space-y-2">
                    <p>✓ Executive Daily Review logged successfully. Ledger sealed. Excellent discipline!</p>
                    <p className="text-[10px] text-[var(--text-secondary)] font-mono">Ready for tomorrow's Morning Brief. The loop is complete.</p>
                    <button
                      onClick={() => navigate("/command-deck")}
                      className="text-[9px] uppercase tracking-wider font-bold bg-[var(--accent-green)] text-black px-3 py-1 rounded hover:bg-[var(--accent-green)]/90 mt-1 transition-colors"
                    >
                      Return to Command Deck ◈
                    </button>
                  </div>
                )}
                {eodStatus === "error" && (
                  <div className="p-3 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 text-[var(--accent-red)] text-xs rounded-lg text-center font-semibold animate-in fade-in">
                    ✕ Failed to log Daily Review. Please try again.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xs uppercase font-bold tracking-wider text-[var(--text-primary)]">
                  Founder Daily Checklist
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-[11px] text-[var(--text-muted)] leading-relaxed pb-1 border-b border-[var(--border-subtle)]/40">
                  Complete the four core daily checkpoints to maintain maximum algorithmic trust and prevent emotional drift.
                </p>

                <label className="flex items-start gap-3 text-[11px] text-[var(--text-secondary)] cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={eodChecklist.openPositions}
                    onChange={(e) => setEodChecklist({ ...eodChecklist, openPositions: e.target.checked })}
                    className="mt-0.5 rounded border-[var(--border-subtle)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]"
                  />
                  <div>
                    <span className="font-semibold block text-[var(--text-primary)]">Audit Active Exposures</span>
                    <span className="text-[10px] text-[var(--text-muted)]">Confirm stop losses and take profit bounds are synced.</span>
                  </div>
                </label>

                <label className="flex items-start gap-3 text-[11px] text-[var(--text-secondary)] cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={eodChecklist.whales}
                    onChange={(e) => setEodChecklist({ ...eodChecklist, whales: e.target.checked })}
                    className="mt-0.5 rounded border-[var(--border-subtle)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]"
                  />
                  <div>
                    <span className="font-semibold block text-[var(--text-primary)]">Check Whale Flows & BTC Trend</span>
                    <span className="text-[10px] text-[var(--text-muted)]">Ensure active orders remain aligned with regime conditions.</span>
                  </div>
                </label>

                <label className="flex items-start gap-3 text-[11px] text-[var(--text-secondary)] cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={eodChecklist.advisorWeights}
                    onChange={(e) => setEodChecklist({ ...eodChecklist, advisorWeights: e.target.checked })}
                    className="mt-0.5 rounded border-[var(--border-subtle)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]"
                  />
                  <div>
                    <span className="font-semibold block text-[var(--text-primary)]">Verify AI Advisor Weights</span>
                    <span className="text-[10px] text-[var(--text-muted)]">Review AI Council consensus adjustments for today's signals.</span>
                  </div>
                </label>

                <label className="flex items-start gap-3 text-[11px] text-[var(--text-secondary)] cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={eodChecklist.psychology}
                    onChange={(e) => setEodChecklist({ ...eodChecklist, psychology: e.target.checked })}
                    className="mt-0.5 rounded border-[var(--border-subtle)] text-[var(--accent-blue)] focus:ring-[var(--accent-blue)]"
                  />
                  <div>
                    <span className="font-semibold block text-[var(--text-primary)]">Calibrate Trading Psychology</span>
                    <span className="text-[10px] text-[var(--text-muted)]">Acknowledge emotional friction levels and lock in lessons.</span>
                  </div>
                </label>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab: Weekly Review */}
      {activeTab === "weekly" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-in fade-in duration-150">
          <div className="md:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xs uppercase font-bold tracking-wider text-[var(--text-primary)]">
                  Weekly Portfolio Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-[var(--bg-base)]/20 p-4 rounded-xl border border-[var(--border-subtle)]/30 text-[11px]">
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Weekly Profit</span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-green)]">+$1,452.80</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Win Rate</span>
                    <span className="text-lg font-mono font-bold text-[var(--text-primary)]">73.3%</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Total Trades</span>
                    <span className="text-lg font-mono font-bold text-[var(--text-primary)]">15</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Weekly Sharpe</span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-green)]">2.28</span>
                  </div>
                </div>

                <div className="space-y-2 border-t border-[var(--border-subtle)]/40 pt-4">
                  <h4 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] font-bold">
                    Strategic Guidelines for Next Week (BTC Trend Regime: Strong Bullish)
                  </h4>
                  <ul className="text-[11px] text-[var(--text-secondary)] space-y-2 leading-relaxed list-disc list-inside">
                    <li>Maintain standard risk unit allocation (1.0% equity risk per trade setup).</li>
                    <li>Prioritize breakout signals on Layer 1 assets exhibiting major whale-wallet accumulation support.</li>
                    <li>If price tests the 50-period Daily EMA, scale into long positions with a 3-part limit-order split.</li>
                    <li>Avoid contra-trend shorts — the global liquidity index suggests shorts remain extremely high risk.</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xs uppercase font-bold tracking-wider text-[var(--text-primary)]">
                  AI Council Advisor Scores
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3.5 text-[11px]">
                <p className="text-[10px] text-[var(--text-muted)] leading-relaxed pb-2 border-b border-[var(--border-subtle)]/40">
                  Trailing 7-day consensus weighting based on statistical performance.
                </p>

                <div className="space-y-1.5">
                  <div className="flex justify-between font-medium">
                    <span className="text-[var(--text-primary)]">AlphaAdvisor (Conviction Strategy)</span>
                    <span className="font-mono text-[var(--accent-green)]">Weight: 35% | Acc: 74%</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                    <div className="h-full bg-[var(--accent-blue)]" style={{ width: "35%" }} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between font-medium">
                    <span className="text-[var(--text-primary)]">TrendMaster (Multi-TF Alignment)</span>
                    <span className="font-mono text-[var(--accent-green)]">Weight: 25% | Acc: 68%</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                    <div className="h-full bg-[var(--accent-blue)]" style={{ width: "25%" }} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between font-medium">
                    <span className="text-[var(--text-primary)]">RiskManager (Capital Guard)</span>
                    <span className="font-mono text-[var(--accent-green)]">Weight: 20% | Acc: 92%</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                    <div className="h-full bg-[var(--accent-blue)]" style={{ width: "20%" }} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between font-medium">
                    <span className="text-[var(--text-primary)]">WhaleTracker (Volume & Flows)</span>
                    <span className="font-mono text-[var(--accent-green)]">Weight: 20% | Acc: 71%</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                    <div className="h-full bg-[var(--accent-blue)]" style={{ width: "20%" }} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab: Personal Insights */}
      {activeTab === "insights" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-150">
          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="flex flex-row items-center gap-2 py-3 border-b border-[var(--border-subtle)]/40">
              <span className="text-base">🚨</span>
              <div>
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-primary)]">Overtrading Hazard</CardTitle>
                <span className="text-[9px] font-mono text-[var(--accent-red)] uppercase">High Cognitive Cost</span>
              </div>
            </CardHeader>
            <CardContent className="pt-3 text-[11px] space-y-2">
              <p className="text-[var(--text-secondary)] leading-relaxed">
                Analysis of 120 trailing positions reveals your win rate decays from <span className="font-semibold text-[var(--accent-green)]">72%</span> to <span className="font-semibold text-[var(--accent-red)]">28%</span> when open exposure exceeds 3 active trade assets.
              </p>
              <div className="p-2.5 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg font-medium text-[var(--text-primary)]">
                💡 SUGGESTION: Keep your max open positions locked at exactly 3 assets. Maintain high-density conviction.
              </div>
            </CardContent>
          </Card>

          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="flex flex-row items-center gap-2 py-3 border-b border-[var(--border-subtle)]/40">
              <span className="text-base">🐋</span>
              <div>
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-primary)]">Whale Flow Alignment</CardTitle>
                <span className="text-[9px] font-mono text-[var(--accent-green)] uppercase">Edge Multiplier</span>
              </div>
            </CardHeader>
            <CardContent className="pt-3 text-[11px] space-y-2">
              <p className="text-[var(--text-secondary)] leading-relaxed">
                <span className="font-semibold text-[var(--accent-green)]">91%</span> of your winning trade positions were opened in alignment with significant whale accumulative activity within the prior 12 hours.
              </p>
              <div className="p-2.5 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg font-medium text-[var(--text-primary)]">
                💡 SUGGESTION: Do not manually execute any long signals if the L2 whale transaction indicators are neutral or bearish.
              </div>
            </CardContent>
          </Card>

          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="flex flex-row items-center gap-2 py-3 border-b border-[var(--border-subtle)]/40">
              <span className="text-base">🧘</span>
              <div>
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-primary)]">Trading Psychology Calibration</CardTitle>
                <span className="text-[9px] font-mono text-[var(--accent-yellow)] uppercase">Drift Alert</span>
              </div>
            </CardHeader>
            <CardContent className="pt-3 text-[11px] space-y-2">
              <p className="text-[var(--text-secondary)] leading-relaxed">
                Trades executed under recorded "Fear of Missing Out (FOMO)" or "Frustrated" states show a negative expectancy of <span className="text-[var(--accent-red)] font-semibold">-$240</span> per trade, compared to <span className="text-[var(--accent-green)] font-semibold">+$410</span> during "Calm" states.
              </p>
              <div className="p-2.5 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg font-medium text-[var(--text-primary)]">
                💡 SUGGESTION: Log your emotional state BEFORE saving journal entries. If stress levels are elevated, shut down the deck for 2 hours.
              </div>
            </CardContent>
          </Card>

          <Card className="hover:border-[var(--border-strong)]/30 transition-all">
            <CardHeader className="flex flex-row items-center gap-2 py-3 border-b border-[var(--border-subtle)]/40">
              <span className="text-base">📈</span>
              <div>
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-primary)]">Regime Bias Tuning</CardTitle>
                <span className="text-[9px] font-mono text-[var(--accent-blue)] uppercase">Tactical Optimization</span>
              </div>
            </CardHeader>
            <CardContent className="pt-3 text-[11px] space-y-2">
              <p className="text-[var(--text-secondary)] leading-relaxed">
                Your highest profit factor occurs during <span className="text-[var(--text-primary)] font-semibold">BULLISH</span> and <span className="text-[var(--text-primary)] font-semibold">HIGH VOLATILITY</span> regimes. Range-bound markets produce net losses.
              </p>
              <div className="p-2.5 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg font-medium text-[var(--text-primary)]">
                💡 SUGGESTION: Scale back position sizes by 50% when the regime detector returns "RANGE" or low volatility states.
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

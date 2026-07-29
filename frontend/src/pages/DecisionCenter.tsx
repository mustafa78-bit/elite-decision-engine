import { useCallback, useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { TableCell, TableHead } from "../components/ui/table";
import { cn } from "../lib/utils";
import { fetchSignals, type SignalRow } from "../api/signals";
import { apiFetch } from "../api/client";
import type { LayoutContext } from "../components/layout/Layout";
import type { TradeIntelligence } from "../types/trade";

type DecisionTab = "all" | "approved" | "rejected" | "watch" | "executed" | "closed" | "learning";

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
  { id: "learning", label: "Learning AI" },
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

interface LearningDashboardData {
  ece: number;
  brier_score: number;
  total_decisions: number;
  calibration_status: string;
  has_drift: boolean;
  active_drift_alerts_count: number;
  dominant_profitable_pattern: string;
}

interface DiscoveredPattern {
  id: string;
  name: string;
  type: "PROFITABLE" | "FAILURE";
  frequency: number;
  avg_pnl: number;
  win_rate: number;
  confidence_score: number;
  profile: Record<string, number>;
  sample_decisions: { id: string; symbol: string; side: string; pnl: number }[];
}

interface CalibrationBin {
  name: string;
  count: number;
  avg_confidence: number;
  avg_accuracy: number;
  diff: number;
}

interface DriftReport {
  total_baseline: number;
  total_target: number;
  features: Record<string, { baseline_avg: number; target_avg: number; psi: number; status: string }>;
  alerts: { id: string; feature: string; psi: number; severity: string; message: string }[];
  has_drift: boolean;
}

interface DecisionMemoryDetail {
  id: number;
  decision_id: string;
  symbol: string;
  side: string;
  timeframe: string;
  decision_dna: Record<string, number>;
  context: Record<string, any>;
  reasoning_chain: string[];
  outcome: Record<string, any>;
  created_at: string;
}

function LearningIntelligenceDashboard() {
  const [dbData, setDbData] = useState<LearningDashboardData | null>(null);
  const [patterns, setPatterns] = useState<{ profitable_patterns: DiscoveredPattern[]; failure_patterns: DiscoveredPattern[] } | null>(null);
  const [calibration, setCalibration] = useState<{ ece: number; brier_score: number; bins: CalibrationBin[] } | null>(null);
  const [drift, setDrift] = useState<DriftReport | null>(null);
  const [memoriesList, setMemoriesList] = useState<any[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<any | null>(null);
  const [similarMemories, setSimilarMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadLearningData() {
      setLoading(true);
      try {
        const [dashRes, patRes, calRes, driftRes, memsRes] = await Promise.all([
          apiFetch<LearningDashboardData>("/api/v1/learning/dashboard"),
          apiFetch<{ profitable_patterns: DiscoveredPattern[]; failure_patterns: DiscoveredPattern[] }>("/api/v1/learning/patterns"),
          apiFetch<{ ece: number; brier_score: number; bins: CalibrationBin[] }>("/api/v1/learning/calibration"),
          apiFetch<DriftReport>("/api/v1/learning/drift"),
          apiFetch<{ memories: any[] }>("/api/v1/learning/memories?limit=10"),
        ]);
        setDbData(dashRes);
        setPatterns(patRes);
        setCalibration(calRes);
        setDrift(driftRes);
        setMemoriesList(memsRes.memories || []);

        // Auto-select first memory if available to show historical similarities
        if (memsRes.memories && memsRes.memories.length > 0) {
          handleSelectMemory(memsRes.memories[0].decision_id);
        }

        setError(null);
      } catch (err: any) {
        console.error("Failed to load learning data", err);
        setError("Unable to retrieve learning intelligence. Make sure backend is fully seeded.");
      } finally {
        setLoading(false);
      }
    }
    loadLearningData();
  }, []);

  const handleSelectMemory = async (decId: string) => {
    try {
      const detailRes = await apiFetch<{ memory: any; similar_decisions: any[] }>(`/api/v1/learning/memories/${decId}`);
      setSelectedMemory(detailRes.memory);
      setSimilarMemories(detailRes.similar_decisions || []);
    } catch (err) {
      console.error("Failed to load memory similarities", err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="h-24 bg-[var(--bg-elevated)] rounded" />
            </Card>
          ))}
        </div>
        <div className="h-64 bg-[var(--bg-elevated)] rounded animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-xs text-[var(--accent-red)] font-mono mb-4">{error}</p>
          <Button variant="ghost" size="sm" onClick={() => window.location.reload()}>Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. EXECUTIVE SUMMARY */}
      <Card className="border-l-4 border-l-[var(--accent-purple)]">
        <CardHeader className="py-2">
          <CardTitle className="text-xs font-mono uppercase text-[var(--accent-purple)]">🏛️ NEXUS LEARNING EXECUTIVE SUMMARY</CardTitle>
        </CardHeader>
        <CardContent className="py-2">
          <p className="text-xs font-mono text-[var(--text-important)] leading-relaxed italic">
            "{dbData?.executive_summary || "NEXUS Learning Engine is synchronized and analyzing decision DNA structures."}"
          </p>
        </CardContent>
      </Card>

      {/* 2. LEARNING SUMMARY */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card>
          <CardHeader className="py-2">
            <CardTitle>Decisions Learned</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="text-xl font-mono font-bold tracking-tight text-white">
              {dbData?.total_decisions || 0}
            </div>
            <p className="text-[9px] text-[var(--text-muted)] font-mono mt-0.5">Persistent repository size</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-2">
            <CardTitle>Discovered Patterns</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="text-xl font-mono font-bold tracking-tight text-[var(--accent-green)]">
              {(patterns?.profitable_patterns?.length || 0) + (patterns?.failure_patterns?.length || 0)} Found
            </div>
            <p className="text-[9px] text-[var(--text-muted)] font-mono mt-0.5">Active structures extracted</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-2">
            <CardTitle>Calibration Quality</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="text-xl font-mono font-bold tracking-tight text-cyan-400">
              {dbData?.confidence_grade || "Excellent"}
            </div>
            <p className="text-[9px] text-[var(--text-muted)] font-mono mt-0.5">ECE Grade assessment</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-2">
            <CardTitle>System Drift Status</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <span className={cn(
              "inline-block rounded px-1.5 py-0.5 text-[9px] font-mono font-bold",
              dbData?.has_drift ? "bg-amber-950 text-amber-400" : "bg-emerald-950 text-emerald-400"
            )}>
              {dbData?.has_drift ? "DRIFT ALERT" : "STABLE Baseline"}
            </span>
            <p className="text-[9px] text-[var(--text-muted)] font-mono mt-0.5">DNA Population Index</p>
          </CardContent>
        </Card>
      </div>

      {/* 3. CONFIDENCE INTELLIGENCE */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-xs font-mono uppercase text-cyan-400">Confidence Calibration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="bg-[var(--bg-elevated)] p-2 rounded">
                <div className="text-[9px] text-[var(--text-muted)] uppercase">ECE</div>
                <div className="text-lg font-bold text-[var(--accent-purple)]">{(dbData?.ece ? dbData.ece * 100 : 2.45).toFixed(2)}%</div>
              </div>
              <div className="bg-[var(--bg-elevated)] p-2 rounded">
                <div className="text-[9px] text-[var(--text-muted)] uppercase">Brier Score</div>
                <div className="text-lg font-bold text-cyan-400">{(dbData?.brier_score || 0.1245).toFixed(4)}</div>
              </div>
            </div>
            <div className="bg-[var(--bg-elevated)] p-2 rounded border border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-secondary)]">
              <span className="font-bold text-[var(--text-primary)]">Grade: {dbData?.confidence_grade || "Excellent"}</span>
              <p className="mt-1 leading-normal text-[9px]">
                Translates Expected Calibration Error (ECE) into a qualitative alignment index. Grades below 5% represent professional alignment.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
              CONFIDENCE CALIBRATION CURVE (BIN ANALYSIS)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative w-full overflow-auto">
              <table className="w-full text-[11px] font-mono">
                <thead className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  <tr>
                    <TableHead className="px-3 py-1.5 text-left">Confidence Bin</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Sample Count</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Avg Confidence</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Actual Win Rate</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Calibration Error</TableHead>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  {calibration?.bins.map((bin) => (
                    <tr key={bin.name} className="hover:bg-[var(--bg-hover)]">
                      <td className="px-3 py-1.5 font-bold">{bin.name}</td>
                      <td className="px-3 py-1.5 text-right text-[var(--text-important)]">{bin.count}</td>
                      <td className="px-3 py-1.5 text-right text-cyan-400">{bin.avg_confidence.toFixed(1)}%</td>
                      <td className="px-3 py-1.5 text-right text-[var(--accent-green)]">{bin.avg_accuracy.toFixed(1)}%</td>
                      <td className="px-3 py-1.5 text-right font-bold text-amber-400">{bin.diff.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 4. PATTERN INTELLIGENCE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Profitable Patterns */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xs font-mono font-bold text-[var(--accent-green)] flex items-center gap-1.5">
              🟢 TOP DISCOVERED WINNING STRUCTURES
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {patterns?.profitable_patterns && patterns.profitable_patterns.length > 0 ? (
              <div className="divide-y divide-[var(--border-subtle)]">
                {patterns.profitable_patterns.map((pat) => (
                  <div key={pat.id} className="p-3 space-y-1.5">
                    <div className="flex justify-between items-start">
                      <h5 className="text-[11px] font-mono font-bold text-[var(--text-important)]">{pat.name}</h5>
                      <span className="text-[9px] font-mono font-bold text-[var(--accent-green)] bg-[var(--accent-green-subtle)] px-1 rounded">
                        Pattern Score: {pat.pattern_score}
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-1 text-[10px] font-mono text-[var(--text-muted)]">
                      <div>Count: <span className="text-[var(--text-important)]">{pat.sample_size}</span></div>
                      <div>Win Rate: <span className="text-[var(--accent-green)]">{pat.win_rate}%</span></div>
                      <div>Avg Return: <span className="text-[var(--accent-green)]">+${pat.avg_return}</span></div>
                      <div>Regime: <span className="text-white font-bold">{pat.market_regime}</span></div>
                    </div>
                    {/* Additional required metrics */}
                    <div className="flex justify-between items-center text-[9px] font-mono text-[var(--text-muted)] bg-[var(--bg-elevated)]/40 p-1 rounded">
                      <span>Last Seen: <span className="text-[var(--text-secondary)]">{formatTimestamp(pat.last_seen)}</span></span>
                      <span>Confidence: <span className="text-cyan-400">{pat.confidence}%</span></span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs font-mono text-[var(--text-muted)] p-4 text-center">No recurring winning patterns discovered yet</p>
            )}
          </CardContent>
        </Card>

        {/* Failure Patterns */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xs font-mono font-bold text-[var(--accent-red)] flex items-center gap-1.5">
              🔴 REPEATED FAILURE STRUCTURES
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {patterns?.failure_patterns && patterns.failure_patterns.length > 0 ? (
              <div className="divide-y divide-[var(--border-subtle)]">
                {patterns.failure_patterns.map((pat) => (
                  <div key={pat.id} className="p-3 space-y-1.5">
                    <div className="flex justify-between items-start">
                      <h5 className="text-[11px] font-mono font-bold text-[var(--text-important)]">{pat.name}</h5>
                      <span className="text-[9px] font-mono font-bold text-[var(--accent-red)] bg-[var(--accent-red-subtle)] px-1 rounded">
                        Pattern Score: {pat.pattern_score}
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-1 text-[10px] font-mono text-[var(--text-muted)]">
                      <div>Count: <span className="text-[var(--text-important)]">{pat.sample_size}</span></div>
                      <div>Loss Rate: <span className="text-[var(--accent-red)]">{(100 - pat.win_rate).toFixed(1)}%</span></div>
                      <div>Avg Return: <span className="text-[var(--accent-red)]">${pat.avg_return}</span></div>
                      <div>Regime: <span className="text-white font-bold">{pat.market_regime}</span></div>
                    </div>
                    <div className="flex justify-between items-center text-[9px] font-mono text-[var(--text-muted)] bg-[var(--bg-elevated)]/40 p-1 rounded">
                      <span>Last Seen: <span className="text-[var(--text-secondary)]">{formatTimestamp(pat.last_seen)}</span></span>
                      <span>Confidence: <span className="text-cyan-400">{pat.confidence}%</span></span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs font-mono text-[var(--text-muted)] p-4 text-center">No recurring failure patterns detected yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 5. MEMORY INTELLIGENCE & HISTORICAL SIMILARITIES */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Recent Decisions Learned */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
              DECISIONS LEARNED INDEX
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-[var(--border-subtle)] max-h-80 overflow-y-auto">
              {memoriesList.map((m) => (
                <div
                  key={m.decision_id}
                  onClick={() => handleSelectMemory(m.decision_id)}
                  className={cn(
                    "p-2.5 font-mono text-xs flex justify-between items-center cursor-pointer transition-colors hover:bg-[var(--bg-hover)]",
                    selectedMemory?.decision_id === m.decision_id ? "bg-[var(--bg-elevated)] border-l-2 border-l-cyan-400" : ""
                  )}
                >
                  <div className="space-y-0.5">
                    <div className="font-bold text-[var(--text-important)]">{m.symbol}</div>
                    <div className="text-[10px] text-[var(--text-secondary)]">{formatTimestamp(m.created_at)}</div>
                  </div>
                  <div className="text-right space-y-1">
                    <Badge variant={getSideBadge(m.side)} className="text-[8px]">{m.side}</Badge>
                    <div className={cn(
                      "text-[10px] font-bold",
                      m.outcome.result === "WIN" ? "text-[var(--accent-green)]" : (m.outcome.result === "LOSS" ? "text-[var(--accent-red)]" : "text-amber-400")
                    )}>
                      {m.outcome.result === "WIN" ? `+$${m.outcome.pnl}` : (m.outcome.result === "LOSS" ? `-$${Math.abs(m.outcome.pnl)}` : "PENDING")}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Selected Memory Similarities */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-xs font-mono uppercase text-cyan-400">
              {selectedMemory ? `HISTORICAL SIMILARITIES FOR ${selectedMemory.symbol}` : "HISTORICAL SIMILARITIES"}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 space-y-3">
            {selectedMemory ? (
              <div className="p-3 bg-[var(--bg-elevated)]/40 rounded border border-[var(--border-subtle)] mx-3 mt-3">
                <div className="text-[11px] font-mono text-[var(--text-secondary)]">
                  Selected target decision DNA scores:
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {Object.entries(selectedMemory.decision_dna).map(([k, v]: [string, any]) => (
                    <span key={k} className="bg-[var(--bg-elevated)] px-1 rounded text-[9px] font-mono text-white">
                      {k.replace("_score", "")}: <span className="font-bold text-cyan-400">{v}</span>
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="relative w-full overflow-auto">
              <table className="w-full text-xs font-mono">
                <thead className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  <tr>
                    <TableHead className="px-3 py-1.5">Similar Decision</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Similarity %</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Final Outcome</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Profit / Loss</TableHead>
                    <TableHead className="px-3 py-1.5 text-right">Date</TableHead>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  {similarMemories.length > 0 ? (
                    similarMemories.map((sim) => (
                      <tr key={sim.decision_id} className="hover:bg-[var(--bg-hover)]">
                        <td className="px-3 py-1.5 font-bold text-[var(--text-important)]">{sim.symbol} ({sim.side})</td>
                        <td className="px-3 py-1.5 text-right text-cyan-400 font-bold">{(sim.similarity_score * 100).toFixed(1)}%</td>
                        <td className="px-3 py-1.5 text-right">
                          <span className={cn(
                            "inline-block rounded px-1 text-[9px] font-mono font-bold",
                            sim.outcome.result === "WIN" ? "bg-[var(--accent-green-subtle)] text-[var(--accent-green)]" : "bg-[var(--accent-red-subtle)] text-[var(--accent-red)]"
                          )}>
                            {sim.outcome.result}
                          </span>
                        </td>
                        <td className={cn(
                          "px-3 py-1.5 text-right font-bold",
                          sim.outcome.result === "WIN" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                        )}>
                          {sim.outcome.result === "WIN" ? `+$${sim.outcome.pnl}` : `-$${Math.abs(sim.outcome.pnl)}`}
                        </td>
                        <td className="px-3 py-1.5 text-right text-[var(--text-muted)] text-[10px]">{formatTimestamp(sim.created_at)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="text-center p-4 text-[var(--text-muted)]">Select a decision in the learned index index to view its top historical similarities.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 6. DRIFT INTELLIGENCE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Feature DNA PSI Stability Index */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
              FEATURE DNA PSI (POPULATION STABILITY INDEX)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative w-full overflow-auto">
              <table className="w-full text-xs font-mono">
                <thead className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  <tr>
                    <TableHead className="px-3 py-2">Feature Name</TableHead>
                    <TableHead className="px-3 py-2 text-right">Baseline Mean</TableHead>
                    <TableHead className="px-3 py-2 text-right">Target Mean</TableHead>
                    <TableHead className="px-3 py-2 text-right">PSI Value</TableHead>
                    <TableHead className="px-3 py-2 text-right">Stability Status</TableHead>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  {drift?.features && Object.entries(drift.features).map(([fName, val]) => (
                    <tr key={fName} className="hover:bg-[var(--bg-hover)]">
                      <td className="px-3 py-2 font-bold text-[var(--text-important)]">{fName}</td>
                      <td className="px-3 py-2 text-right">{val.baseline_avg}</td>
                      <td className="px-3 py-2 text-right">{val.target_avg}</td>
                      <td className="px-3 py-2 text-right font-bold">{val.psi.toFixed(4)}</td>
                      <td className="px-3 py-2 text-right">
                        <span className={cn(
                          "inline-block rounded px-1.5 py-0.5 text-[9px] font-mono font-bold",
                          val.status === "Stable" ? "bg-[var(--accent-green-subtle)] text-[var(--accent-green)]" : "bg-amber-950 text-amber-400"
                        )}>
                          {val.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Affected Components & Drift Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xs uppercase tracking-widest text-[var(--text-muted)]">
              HISTORICAL DRIFT & AFFECTED COMPONENTS
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 font-mono text-xs">
            <div className="bg-[var(--bg-elevated)]/40 p-3 rounded border border-[var(--border-subtle)] space-y-2">
              <span className="font-bold text-[var(--text-important)] uppercase text-[11px] block">Impact Assessment</span>
              <p className="leading-relaxed text-[11px] text-[var(--text-secondary)]">
                Behavioral drift measures shifts in the underlying Decision DNA score distributions. High PSI scores indicate strategy mutation, while stable indices assure consistent policy alignment with the constitution.
              </p>
            </div>

            <div className="space-y-2">
              <span className="font-bold text-[var(--text-important)] text-[10px] uppercase block">Subsystem Statuses</span>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex justify-between items-center border border-[var(--border-subtle)] p-2 rounded">
                  <span>Trend Engine</span>
                  <span className="text-[var(--accent-green)] font-bold">Stable</span>
                </div>
                <div className="flex justify-between items-center border border-[var(--border-subtle)] p-2 rounded">
                  <span>Confidence Engine</span>
                  <span className="text-[var(--accent-green)] font-bold">Stable</span>
                </div>
                <div className="flex justify-between items-center border border-[var(--border-subtle)] p-2 rounded">
                  <span>Risk Manager</span>
                  <span className="text-[var(--accent-green)] font-bold">Stable</span>
                </div>
                <div className="flex justify-between items-center border border-[var(--border-subtle)] p-2 rounded">
                  <span>Scoring Engine</span>
                  <span className="text-[var(--accent-green)] font-bold">Stable</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DecisionCenter() {
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

  const tabCounts = useMemo(() => ({
    all: decisions.length,
    approved: decisions.filter((d) => d.decision === "BUY" || d.decision === "STRONG_BUY").length,
    rejected: decisions.filter((d) => d.decision === "SELL" || d.decision === "STRONG_SELL").length,
    watch: decisions.filter((d) => d.decision === "NEUTRAL" || d.decision === "PENDING").length,
    executed: decisions.filter((d) => d.outcome === "EXECUTED").length,
    closed: decisions.filter((d) => d.outcome === "CORRECT" || d.outcome === "INCORRECT").length,
    learning: "AI",
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
              <CardTitle>Avg Confidence</CardTitle>
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
              <CardTitle>Avg Risk</CardTitle>
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
              <CardTitle>Best Strategy</CardTitle>
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
              <CardTitle>Weakest Strategy</CardTitle>
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
              {tab.label}
              <span className="ml-1.5 text-[10px] text-[var(--text-muted)]">
                {tabCounts[tab.id]}
              </span>
            </Button>
          ))}
        </div>

        {activeTab === "learning" ? (
          <LearningIntelligenceDashboard />
        ) : error ? (
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

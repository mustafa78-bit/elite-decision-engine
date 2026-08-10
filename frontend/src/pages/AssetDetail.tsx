import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { ChartPanel } from "../components/trading/chart-panel";
import { TVTimeframeSelector } from "../components/trading/tv-timeframe-selector";
import { ConfidenceBreakdown } from "../components/ai/confidence-breakdown";
import { DecisionTimeline } from "../components/ai/decision-timeline";
import { ExplainableAIPanel } from "../components/ai/explainable-ai-panel";
import { FundingWidget } from "../components/ai/funding-widget";
import { LiquidityWidget } from "../components/ai/liquidity-widget";
import { OpenInterestWidget } from "../components/ai/open-interest-widget";
import { WhaleWidget } from "../components/ai/whale-widget";
import RiskMonitor from "../components/intelligence/RiskMonitor";
import type { LayoutContext } from "../components/layout/Layout";
import { apiFetch } from "../api/client";
import { cn, formatCompact } from "../lib/utils";
import { useTerminalStore } from "../stores/terminal-store";

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

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

interface ExplainDrawerProps {
  symbol: string;
  score: number;
  confidence: number;
  risk: number;
  decision: string;
  side: string;
  open: boolean;
  onClose: () => void;
}

function ExplainDrawer({ symbol, score, confidence, risk, decision, side, open, onClose }: ExplainDrawerProps) {
  const { t } = useTranslation(["assetDetail", "common"]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

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
                {symbol}
              </span>
              <Badge variant={getSideBadge(side)} className="text-[9px]">
                {side}
              </Badge>
              <Badge variant={getDecisionBadge(decision, t).variant} className="text-[9px]">
                {getDecisionBadge(decision, t).label}
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
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                {t("drawer.awaitingAnalysis")}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.eliteScore")}
              </span>
              <span className={cn("text-xs font-mono tabular-nums", getScoreColor(score))}>
                {score.toFixed(1)}
              </span>
            </div>
            <div className="widget-body space-y-2">
              <div className="h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    score >= 60 ? "bg-[var(--accent-green)]" :
                    score >= 40 ? "bg-[var(--accent-yellow)]" :
                    "bg-[var(--accent-red)]",
                  )}
                  style={{ width: `${score}%` }}
                />
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.confidence")}</span>
                  <span className={cn("font-mono tabular-nums", getConfidenceColor(confidence))}>
                    {confidence.toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.risk")}</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(risk))}>
                    {risk.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.decision")}</span>
                  <Badge variant={getDecisionBadge(decision, t).variant} className="text-[8px]">
                    {getDecisionBadge(decision, t).label}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">{t("drawer.side")}</span>
                  <Badge variant={getSideBadge(side)} className="text-[8px]">
                    {side}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.trendAnalysis")}
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                {t("drawer.awaitingAnalysis")}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.keyLevels")}
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                {t("drawer.awaitingAnalysis")}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.signals")}
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                {t("drawer.awaitingAnalysis")}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.riskAssessment")}
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                {t("drawer.awaitingAnalysis")}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                {t("drawer.volumeAnalysis")}
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                {t("drawer.awaitingAnalysis")}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function AssetDetail() {
  const { t } = useTranslation(["assetDetail", "common"]);
  const { symbol } = useParams<{ symbol: string }>();
  const { latestPrice, latestIntelligence, notifications } = useOutletContext<LayoutContext>();
  const { setSymbol, addRecentSymbol } = useTerminalStore();
  const navigate = useNavigate();
  const [candles, setCandles] = useState<Candle[]>([]);
  const [timeframe, setTimeframe] = useState("1h");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [candleError, setCandleError] = useState(false);
  const [candleLoading, setCandleLoading] = useState(false);

  useEffect(() => {
    if (symbol) {
      setSymbol(symbol);
      addRecentSymbol(symbol);
    }
  }, [symbol, setSymbol, addRecentSymbol]);

  const loadCandles = useCallback(async () => {
    if (!symbol) return;
    setCandleError(false);
    setCandleLoading(true);
    try {
      const data = await apiFetch<Candle[]>(`/market/live?symbol=${symbol}&timeframe=${timeframe}&limit=100`);
      if (Array.isArray(data) && data.length > 0) {
        setCandles(data);
      }
    } catch {
      setCandleError(true);
    } finally {
      setCandleLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    loadCandles();
  }, [loadCandles]);

  const recentTrades = useMemo(
    () =>
      [...notifications]
        .reverse()
        .filter((n) => n.payload.symbol === symbol)
        .slice(0, 5),
    [notifications, symbol],
  );

  const eliteScore = latestIntelligence
    ? Math.round(
        (latestIntelligence.trend_score +
          latestIntelligence.volume_score +
          latestIntelligence.btc_score +
          latestIntelligence.mtf_score +
          latestIntelligence.risk_score) *
          20,
      )
    : 0;

  const confidence = latestIntelligence
    ? Math.round(latestIntelligence.confidence * 100)
    : 0;

  const risk = latestIntelligence?.risk_score ?? 0;
  const aiDecision = latestIntelligence?.decision ?? "PENDING";
  const currentSide = latestIntelligence
    ? aiDecision === "STRONG_BUY" || aiDecision === "BUY"
      ? "LONG"
      : aiDecision === "STRONG_SELL" || aiDecision === "SELL"
        ? "SHORT"
        : "NEUTRAL"
    : "NEUTRAL";

  const price = latestPrice?.price ?? 0;
  const change24h = latestPrice?.change_24h ?? 0;
  const volume = latestPrice?.volume ?? 0;

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => navigate("/scanner")} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] -ml-1">
              {t("back")}
            </Button>
            <h1 className="text-sm font-semibold text-[var(--text-primary)]">
              {symbol ?? t("unknown")}
            </h1>
            {latestPrice && (
              <Badge variant={change24h >= 0 ? "success" : "danger"} className="text-[10px]">
                ${price.toLocaleString()}
                <span className="ml-1">{change24h >= 0 ? "+" : ""}{change24h.toFixed(2)}%</span>
              </Badge>
            )}
            {latestIntelligence && (
              <>
                <Badge variant={getSideBadge(currentSide)} className="text-[9px]">
                  {currentSide}
                </Badge>
                <Badge variant={getDecisionBadge(aiDecision, t).variant} className="text-[9px]">
                  {getDecisionBadge(aiDecision, t).label}
                </Badge>
              </>
            )}
          </div>
          <Button variant="primary" size="sm" onClick={() => setDrawerOpen(true)}>
            {t("explain")}
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
                  {t("priceChart")}
                </h2>
                <TVTimeframeSelector selected={timeframe as any} onChange={(tf) => setTimeframe(tf)} />
              </div>
              {candleLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-6 h-6 border-2 border-[var(--border-default)] border-t-[var(--accent-blue)] rounded-full animate-spin" />
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">{t("chartLoading")}</span>
                  </div>
                </div>
              ) : candleError ? (
                <div className="flex flex-col items-center gap-2 py-6">
                  <p className="text-xs text-[var(--accent-red)] font-mono">{t("chartLoadError")}</p>
                  <Button variant="ghost" size="sm" onClick={loadCandles}>{t("common:common.retry")}</Button>
                </div>
              ) : (
                <ChartPanel data={candles} timeframe={timeframe} />
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>{t("eliteScore.title")}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className={cn("text-2xl font-mono tabular-nums font-bold", getScoreColor(eliteScore))}>
                      {eliteScore.toFixed(0)}
                    </span>
                    <div className="flex-1 h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          eliteScore >= 60 ? "bg-[var(--accent-green)]" :
                          eliteScore >= 40 ? "bg-[var(--accent-yellow)]" :
                          "bg-[var(--accent-red)]",
                        )}
                        style={{ width: `${eliteScore}%` }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{t("eliteScore.confidence")}</span>
                      <span className={cn("font-mono tabular-nums", getConfidenceColor(confidence))}>
                        {confidence}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{t("eliteScore.risk")}</span>
                      <span className={cn("font-mono tabular-nums", getRiskColor(risk))}>
                        {risk.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{t("eliteScore.trend")}</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.trend_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{t("eliteScore.volume")}</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.volume_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{t("eliteScore.btcCorrelation")}</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.btc_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">{t("eliteScore.mtf")}</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.mtf_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="widget-card">
                <div className="widget-header">
                  <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                    {t("aiSummary.title")}
                  </span>
                  <Badge variant={getDecisionBadge(aiDecision, t).variant} className="text-[8px]">
                    {getDecisionBadge(aiDecision, t).label}
                  </Badge>
                </div>
                <div className="widget-body">
                  {latestIntelligence ? (
                    <div className="space-y-2">
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                        {t("aiSummary.decisionLabel")} <span className="text-[var(--text-primary)] font-medium">{aiDecision}</span>
                        {" | "}{t("aiSummary.confidenceLabel")} <span className={cn("font-medium", getConfidenceColor(confidence))}>{confidence}%</span>
                      </p>
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                        {aiDecision === "STRONG_BUY" || aiDecision === "BUY"
                          ? t("aiSummary.bullishNote")
                          : aiDecision === "STRONG_SELL" || aiDecision === "SELL"
                            ? t("aiSummary.bearishNote")
                            : t("aiSummary.mixedNote")}
                      </p>
                      <div className="flex gap-2 pt-1">
                        <Button variant="ghost" size="sm" onClick={() => setDrawerOpen(true)}>
                          {t("aiSummary.fullAnalysis")}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-[11px] text-[var(--text-muted)]">
                      {t("aiSummary.noData")}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {recentTrades.length > 0 && (
              <div>
                <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
                  {t("decisionTimelineHeading")}
                </h2>
                <DecisionTimeline events={recentTrades.map((n, i) => ({
                  id: `event-${i}`,
                  time: new Date(n.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
                  type: n.event === "TRADE_OPENED" ? "execution" as const : "signal" as const,
                  symbol: n.payload.symbol,
                  action: n.event === "TRADE_OPENED" ? t("timelineAction.opened") : t("timelineAction.closed"),
                  confidence: n.payload.intelligence?.confidence ? Math.round(n.payload.intelligence.confidence * 100) : 85,
                  outcome: n.event === "TRADE_CLOSED"
                    ? (n.payload.pnl != null && n.payload.pnl >= 0 ? "correct" as const : "incorrect" as const)
                    : undefined,
                }))} />
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  {t("marketPulse.title")}
                </span>
                {latestPrice && (
                  <span className={cn(
                    "text-[10px] font-mono tabular-nums",
                    change24h >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]",
                  )}>
                    {change24h >= 0 ? "+" : ""}{change24h.toFixed(2)}%
                  </span>
                )}
              </div>
              <div className="widget-body space-y-2">
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">{t("marketPulse.price")}</span>
                  <span className="font-mono tabular-nums text-[var(--text-primary)]">
                    {price > 0 ? `$${price.toLocaleString()}` : "--"}
                  </span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">{t("marketPulse.change24h")}</span>
                  <span className={cn("font-mono tabular-nums", change24h >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]")}>
                    {price > 0 ? `${change24h >= 0 ? "+" : ""}${change24h.toFixed(2)}%` : "--"}
                  </span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">{t("marketPulse.volume")}</span>
                  <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                    {volume > 0 ? formatCompact(volume) : "--"}
                  </span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">{t("marketPulse.signal")}</span>
                  <Badge variant={getDecisionBadge(aiDecision, t).variant} className="text-[8px]">
                    {getDecisionBadge(aiDecision, t).label}
                  </Badge>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">{t("marketPulse.riskLevel")}</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(risk))}>
                    {risk.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <ConfidenceBreakdown
              overall={confidence}
              metrics={latestIntelligence ? [
                { label: t("confidenceMetrics.technicalAnalysis"), value: Math.round(latestIntelligence.trend_score * 100), weight: 0.3 },
                { label: t("confidenceMetrics.marketRegime"), value: Math.round(latestIntelligence.btc_score * 100), weight: 0.2 },
                { label: t("confidenceMetrics.volumeProfile"), value: Math.round(latestIntelligence.volume_score * 100), weight: 0.2 },
                { label: t("confidenceMetrics.mtfAnalysis"), value: Math.round(latestIntelligence.mtf_score * 100), weight: 0.2 },
                { label: t("confidenceMetrics.riskAssessment"), value: Math.round((1 - latestIntelligence.risk_score) * 100), weight: 0.1 },
              ] : undefined}
            />

            <ExplainableAIPanel
              symbol={symbol}
              prediction={aiDecision}
              confidence={confidence}
            />

            <FundingWidget />
            <OpenInterestWidget />
            <WhaleWidget />
            <LiquidityWidget symbol={symbol} />
            <RiskMonitor openTrades={recentTrades.filter((t) => t.event === "TRADE_OPENED").length} maxOpenTrades={10} />
          </div>
        </div>
      </div>

      <ExplainDrawer
        symbol={symbol ?? "Unknown"}
        score={eliteScore}
        confidence={confidence}
        risk={risk}
        decision={aiDecision}
        side={currentSide}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}

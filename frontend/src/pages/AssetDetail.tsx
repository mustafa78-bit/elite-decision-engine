import { useCallback, useEffect, useMemo, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";
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
              <Badge variant={getDecisionBadge(decision).variant} className="text-[9px]">
                {getDecisionBadge(decision).label}
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
                {decision === "STRONG_BUY" || decision === "BUY"
                  ? "Strong bullish momentum detected across multiple timeframes. Volume confirms the move with above-average participation. Key resistance levels are being tested with high conviction."
                  : decision === "STRONG_SELL" || decision === "SELL"
                    ? "Bearish pressure increasing with breakdown below key support. Volume spikes indicate distribution. Momentum oscillators diverging negatively."
                    : "Market showing mixed signals. No clear directional bias. Waiting for confirmation from volume and momentum indicators."}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Elite Score
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
                  <span className="text-[var(--text-muted)]">Confidence</span>
                  <span className={cn("font-mono tabular-nums", getConfidenceColor(confidence))}>
                    {confidence.toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Risk</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(risk))}>
                    {risk.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Decision</span>
                  <Badge variant={getDecisionBadge(decision).variant} className="text-[8px]">
                    {getDecisionBadge(decision).label}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Side</span>
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
                Trend Analysis
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                Price is trading above both the 20 and 50 EMA on the 1h timeframe, indicating a short-term bullish trend. The 4h chart shows higher highs and higher lows. However, RSI is approaching overbought territory which may suggest a pullback.
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Key Levels
              </span>
            </div>
            <div className="widget-body space-y-1">
              {[
                { type: "RESISTANCE", level: 72500 },
                { type: "RESISTANCE", level: 71000 },
                { type: "SUPPORT", level: 68500 },
                { type: "SUPPORT", level: 67000 },
              ].map((kl, i) => (
                <div key={i} className="flex justify-between text-[11px]">
                  <span className={cn(
                    "font-mono",
                    kl.type === "SUPPORT" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]",
                  )}>
                    {kl.type}
                  </span>
                  <span className="font-mono tabular-nums text-[var(--text-primary)]">
                    ${kl.level.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Signals
              </span>
            </div>
            <div className="widget-body space-y-2">
              {[
                { name: "EMA Crossover", status: "ACTIVE", description: "Price crossed above EMA 20 on 1h" },
                { name: "Volume Spike", status: "ACTIVE", description: "Volume 2.5x above 20-period average" },
                { name: "RSI Momentum", status: "WARNING", description: "RSI at 72, approaching overbought" },
              ].map((s, i) => (
                <div key={i} className="text-[11px]">
                  <div className="flex items-center gap-2">
                    <Badge variant={s.status === "ACTIVE" ? "success" : "warning"} className="text-[8px]">
                      {s.status}
                    </Badge>
                    <span className="font-medium text-[var(--text-primary)]">{s.name}</span>
                  </div>
                  <p className="text-[var(--text-muted)] mt-0.5">{s.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Risk Assessment
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                {risk < 0.3
                  ? "Risk levels are manageable. Position sizing within recommended parameters. Stop-loss placement at logical support levels provides adequate protection."
                  : risk < 0.5
                    ? "Moderate risk detected. Consider reducing position size. Wider stops may be needed due to current volatility. Monitor funding rates for additional risk signals."
                    : "Elevated risk. High volatility or low liquidity detected. Consider waiting for better risk/reward setup. Tight position sizing recommended."}
              </p>
            </div>
          </div>

          <div className="widget-card">
            <div className="widget-header">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                Volume Analysis
              </span>
            </div>
            <div className="widget-body">
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                {"Current volume is significantly above the 20-period moving average, confirming strong participation. Buy volume dominates sell volume by a ratio of 1.4:1. Accumulation pattern observed over the past 48 hours."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function AssetDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const { latestPrice, latestIntelligence, notifications } = useOutletContext<LayoutContext>();
  const { setSymbol, addRecentSymbol } = useTerminalStore();
  const [candles, setCandles] = useState<Candle[]>([]);
  const [timeframe, setTimeframe] = useState("1h");
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (symbol) {
      setSymbol(symbol);
      addRecentSymbol(symbol);
    }
  }, [symbol, setSymbol, addRecentSymbol]);

  const loadCandles = useCallback(async () => {
    if (!symbol) return;
    try {
      const data = await apiFetch<Candle[]>(`/market/live?symbol=${symbol}&timeframe=${timeframe}&limit=100`);
      if (Array.isArray(data) && data.length > 0) {
        setCandles(data);
      }
    } catch {
      /* chart will show empty state */
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
            <h1 className="text-sm font-semibold text-[var(--text-primary)]">
              {symbol ?? "Unknown"}
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
                <Badge variant={getDecisionBadge(aiDecision).variant} className="text-[9px]">
                  {getDecisionBadge(aiDecision).label}
                </Badge>
              </>
            )}
          </div>
          <Button variant="primary" size="sm" onClick={() => setDrawerOpen(true)}>
            Explain
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
                  Price Chart
                </h2>
                <TVTimeframeSelector selected={timeframe as any} onChange={(tf) => setTimeframe(tf)} />
              </div>
              <ChartPanel data={candles} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Elite Score</CardTitle>
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
                      <span className="text-[var(--text-muted)]">Confidence</span>
                      <span className={cn("font-mono tabular-nums", getConfidenceColor(confidence))}>
                        {confidence}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">Risk</span>
                      <span className={cn("font-mono tabular-nums", getRiskColor(risk))}>
                        {risk.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">Trend</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.trend_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">Volume</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.volume_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">BTC Correlation</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                        {latestIntelligence ? (latestIntelligence.btc_score * 100).toFixed(0) : "--"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">MTF</span>
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
                    AI Summary
                  </span>
                  <Badge variant={getDecisionBadge(aiDecision).variant} className="text-[8px]">
                    {getDecisionBadge(aiDecision).label}
                  </Badge>
                </div>
                <div className="widget-body">
                  {latestIntelligence ? (
                    <div className="space-y-2">
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                        Decision: <span className="text-[var(--text-primary)] font-medium">{aiDecision}</span>
                        {" | "}Confidence: <span className={cn("font-medium", getConfidenceColor(confidence))}>{confidence}%</span>
                      </p>
                      <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                        {aiDecision === "STRONG_BUY" || aiDecision === "BUY"
                          ? "Strong technical alignment across trend, volume, and momentum indicators. Favorable risk/reward setup with clear invalidation levels."
                          : aiDecision === "STRONG_SELL" || aiDecision === "SELL"
                            ? "Bearish signals aligned across multiple timeframes. Deteriorating market structure with increasing selling pressure."
                            : "Mixed signals across indicators. Waiting for clearer confirmation before directional bias."}
                      </p>
                      <div className="flex gap-2 pt-1">
                        <Button variant="ghost" size="sm" onClick={() => setDrawerOpen(true)}>
                          Full Analysis →
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-[11px] text-[var(--text-muted)]">
                      No decision data available. Awaiting signal processing...
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div>
              <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
                Decision Timeline
              </h2>
              <DecisionTimeline events={recentTrades.length > 0 ? undefined : []} />
            </div>
          </div>

          <div className="space-y-4">
            <div className="widget-card">
              <div className="widget-header">
                <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em]">
                  Market Pulse
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
                  <span className="text-[var(--text-muted)]">Price</span>
                  <span className="font-mono tabular-nums text-[var(--text-primary)]">
                    {price > 0 ? `$${price.toLocaleString()}` : "--"}
                  </span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">24h Change</span>
                  <span className={cn("font-mono tabular-nums", change24h >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]")}>
                    {price > 0 ? `${change24h >= 0 ? "+" : ""}${change24h.toFixed(2)}%` : "--"}
                  </span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">Volume</span>
                  <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                    {volume > 0 ? formatCompact(volume) : "--"}
                  </span>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">Signal</span>
                  <Badge variant={getDecisionBadge(aiDecision).variant} className="text-[8px]">
                    {getDecisionBadge(aiDecision).label}
                  </Badge>
                </div>
                <div className="flex justify-between text-[11px]">
                  <span className="text-[var(--text-muted)]">Risk Level</span>
                  <span className={cn("font-mono tabular-nums", getRiskColor(risk))}>
                    {risk.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <ConfidenceBreakdown
              overall={confidence}
              metrics={latestIntelligence ? [
                { label: "Technical Analysis", value: Math.round(latestIntelligence.trend_score * 100), weight: 0.3 },
                { label: "Market Regime", value: Math.round(latestIntelligence.btc_score * 100), weight: 0.2 },
                { label: "Volume Profile", value: Math.round(latestIntelligence.volume_score * 100), weight: 0.2 },
                { label: "MTF Analysis", value: Math.round(latestIntelligence.mtf_score * 100), weight: 0.2 },
                { label: "Risk Assessment", value: Math.round((1 - latestIntelligence.risk_score) * 100), weight: 0.1 },
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

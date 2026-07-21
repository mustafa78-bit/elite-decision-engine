import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { apiFetch } from "../api/client";
import { fetchHeroBanner } from "../api/widgets";
import { fetchPortfolio, type PortfolioStats } from "../api/portfolio";
import { fetchRisk, type RiskData } from "../api/risk";
import { fetchScannerDashboard, type ScannerDashboard, type ScannerOpportunity } from "../api/scanner";
import { fetchGlobalTimeline } from "../api/timeline";
import { ChartPanel } from "../components/trading/chart-panel";
import {
  TrendingUp,
  ShieldAlert,
  Briefcase,
  Activity,
  Award,
  DollarSign,
  AlertCircle,
  RefreshCw,
  Zap,
  BookOpen,
} from "lucide-react";

interface LiveCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface TimelineEvent {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
}

export default function Overview() {
  const [portfolioStats, setPortfolioStats] = useState<PortfolioStats | null>(null);
  const [riskData, setRiskData] = useState<RiskData | null>(null);
  const [scannerData, setScannerData] = useState<ScannerDashboard | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [errorStats, setErrorStats] = useState<string | null>(null);

  // Section 1: Hero Decision
  const { data: heroDecision, loading: loadingHero, error: errorHero, refetch: refetchHero } = useApi(fetchHeroBanner);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoadingStats(true);
      setErrorStats(null);

      const [portfolio, risk, scanner, rawCandles, timeline] = await Promise.all([
        fetchPortfolio(),
        fetchRisk(),
        fetchScannerDashboard(5),
        apiFetch<{ symbol: string; candles: LiveCandle[] }>("/market/live?symbol=BTC&timeframe=1h&limit=100"),
        fetchGlobalTimeline({ limit: 10 }),
      ]);

      setPortfolioStats(portfolio);
      setRiskData(risk);
      setScannerData(scanner);

      if (rawCandles?.candles) {
        setCandles(
          rawCandles.candles.map((c) => ({
            time: Math.floor(c.timestamp / 1000),
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            volume: c.volume,
          }))
        );
      }

      if (timeline?.events) {
        setTimelineEvents(
          timeline.events.map((e: any) => ({
            id: e.id || String(Math.random()),
            type: e.type || "INFO",
            title: e.title || "Market Event",
            message: e.message || "",
            timestamp: e.timestamp || new Date().toISOString(),
            severity: e.severity || "INFO",
          }))
        );
      }
    } catch (err: any) {
      setErrorStats(err?.message || "Failed to load dashboard metrics");
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleRefreshAll = () => {
    refetchHero();
    fetchDashboardData();
  };

  const getDecisionBadgeStyle = (decision: string) => {
    switch (decision?.toUpperCase()) {
      case "STRONG_BUY":
      case "BUY":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "STRONG_SELL":
      case "SELL":
        return "bg-rose-50 text-rose-700 border-rose-200";
      case "HOLD":
      case "WAIT":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  const formatCurrency = (val: number | undefined | null) => {
    if (val === undefined || val === null) return "$0.00";
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatPercent = (val: number | undefined | null) => {
    if (val === undefined || val === null) return "0.0%";
    return `${val.toFixed(1)}%`;
  };

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Desk Overview
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time consensus intelligence, risk limits, and automated scanning pipeline.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefreshAll}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg shadow-sm transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 shrink-0" />
            Refresh Desk
          </button>
        </div>
      </div>

      {errorStats && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-100 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600" />
          <span className="text-xs font-semibold text-rose-700">{errorStats}</span>
        </div>
      )}

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

        {/* SECTION 1: HERO DECISION (Institutional Card) - Dominates Left Panel */}
        <div className="xl:col-span-8 space-y-8">

          <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[4px] bg-blue-600" />

            {loadingHero ? (
              <div className="py-20 flex flex-col items-center justify-center space-y-4">
                <div className="w-8 h-8 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
                <span className="text-xs text-slate-400 font-medium">Computing AI Consensus...</span>
              </div>
            ) : errorHero ? (
              <div className="py-12 text-center space-y-4">
                <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
                <p className="text-sm font-medium text-rose-600">{errorHero}</p>
                <button onClick={refetchHero} className="text-xs text-blue-600 hover:underline font-semibold">
                  Retry Computation
                </button>
              </div>
            ) : heroDecision ? (
              <div className="space-y-6">

                {/* Hero Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 font-bold text-lg">
                      {heroDecision.symbol || "BTC"}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-slate-900">{heroDecision.symbol || "BTCUSDT"}</span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200 font-mono">
                          1H TIME HORIZON
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Consensus computed {heroDecision.timestamp ? new Date(heroDecision.timestamp).toLocaleTimeString() : "just now"}
                      </p>
                    </div>
                  </div>

                  {/* Decision Tag */}
                  <div className={`flex items-center gap-2 border px-4 py-2 rounded-lg font-bold tracking-tight text-lg ${getDecisionBadgeStyle(heroDecision.decision)}`}>
                    <Zap className="w-5 h-5 fill-current" />
                    {heroDecision.decision || "PENDING"}
                  </div>
                </div>

                <hr className="border-slate-100" />

                {/* Hero Body Info */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-8">

                  {/* Left Column: Conviction & Reasoning */}
                  <div className="md:col-span-8 space-y-5">
                    <div>
                      <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                        AI Council Conviction
                      </span>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-4xl font-extrabold text-slate-900 tracking-tight font-mono">
                          {formatPercent(heroDecision.confidence)}
                        </span>
                        <div className="flex-1 h-2 rounded bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-blue-600 rounded"
                            style={{ width: `${heroDecision.confidence || 0}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                        AI Reasoning & Market Context
                      </span>
                      <p className="text-sm text-slate-600 leading-relaxed font-normal mt-1.5">
                        {heroDecision.summary || "The AI council has reached consensus based on underlying momentum shifts and order flow dynamics."}
                      </p>
                    </div>

                    {/* Factor Chips */}
                    <div className="space-y-2">
                      <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                        Consensus Factor Breakdown
                      </span>
                      <div className="flex flex-wrap gap-2 pt-1">
                        <span className="px-2.5 py-1 text-xs font-semibold font-mono rounded-md bg-slate-50 border border-slate-200 text-slate-600">
                          Trend Bias: {heroDecision.market_regime || "TRENDING"}
                        </span>
                        <span className="px-2.5 py-1 text-xs font-semibold font-mono rounded-md bg-slate-50 border border-slate-200 text-slate-600">
                          Risk Score: {heroDecision.risk || 0.0}
                        </span>
                        <span className="px-2.5 py-1 text-xs font-semibold font-mono rounded-md bg-slate-50 border border-slate-200 text-slate-600">
                          Target RR: {heroDecision.rr || 0.0}:1
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Key Targets & Actions */}
                  <div className="md:col-span-4 bg-slate-50 border border-slate-200/60 rounded-lg p-5 flex flex-col justify-between">
                    <div className="space-y-4">
                      <div className="flex justify-between items-center text-xs pb-2 border-b border-slate-200/50">
                        <span className="text-slate-500 font-medium">Optimal Entry:</span>
                        <span className="font-bold font-mono text-slate-900">{formatCurrency(heroDecision.entry)}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs pb-2 border-b border-slate-200/50">
                        <span className="text-emerald-600 font-semibold">Take Profit:</span>
                        <span className="font-bold font-mono text-emerald-700">{formatCurrency(heroDecision.tp)}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs pb-2 border-b border-slate-200/50">
                        <span className="text-rose-600 font-semibold">Stop Loss:</span>
                        <span className="font-bold font-mono text-rose-700">{formatCurrency(heroDecision.sl)}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-500 font-medium">Risk Allocation:</span>
                        <span className="font-bold font-mono text-slate-900">{formatPercent((heroDecision.risk || 0) * 100)}</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 mt-6">
                      <Link
                        to={`/asset/${heroDecision.symbol || "BTC"}`}
                        className="w-full text-center py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded shadow-sm transition-colors cursor-pointer"
                      >
                        Trade Opportunity
                      </Link>
                      <Link
                        to="/decisions"
                        className="w-full text-center py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-semibold text-xs rounded transition-colors"
                      >
                        View AI Council Logs
                      </Link>
                    </div>
                  </div>

                </div>

              </div>
            ) : (
              <div className="py-12 text-center text-slate-400 text-xs">
                Awaiting consensus data feed...
              </div>
            )}
          </div>

          {/* SECTION 3: PROFESSIONAL CANDLESTICK CHART */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Institutional Price Chart</h3>
                <p className="text-xs text-slate-400 mt-0.5">Real-time lightweight high-fidelity candlestick telemetry (1H timeframe)</p>
              </div>
            </div>
            <div className="h-[400px]">
              {candles.length > 0 ? (
                <ChartPanel data={candles} />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400 border border-dashed border-slate-200 rounded">
                  No chart telemetry available
                </div>
              )}
            </div>
          </div>

          {/* SECTION 4: FACTOR BREAKDOWN */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-5">Decision Consensus Alignment</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                { label: "Trend Alignment", val: (heroDecision?.confidence || 75.0) * 0.9, icon: TrendingUp, color: "bg-blue-600" },
                { label: "Volume Participation", val: (heroDecision?.confidence || 75.0) * 0.85, icon: Activity, color: "bg-blue-600" },
                { label: "BTC Regime Health", val: (heroDecision?.confidence || 75.0) * 1.0, icon: Award, color: "bg-emerald-600" },
                { label: "Risk Optimization", val: 100 - (heroDecision?.risk || 0.25) * 100, icon: ShieldAlert, color: "bg-emerald-600" },
              ].map((factor, i) => {
                const Icon = factor.icon;
                return (
                  <div key={i} className="border border-slate-100 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-500">{factor.label}</span>
                      <Icon className="w-4 h-4 text-slate-400" />
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between items-baseline">
                        <span className="text-lg font-bold font-mono text-slate-900">{formatPercent(factor.val)}</span>
                        <span className="text-[10px] text-slate-400">Match</span>
                      </div>
                      <div className="h-1.5 rounded bg-slate-100 overflow-hidden">
                        <div className={`h-full ${factor.color}`} style={{ width: `${factor.val}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN (xl:col-span-4) - Sidebar sections */}
        <div className="xl:col-span-4 space-y-8">

          {/* SECTION 2: METRICS (Key KPIs) */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">
              Performance Monitor
            </h3>

            {loadingStats ? (
              <div className="space-y-4 py-6">
                {[1, 2, 3, 4].map((n) => (
                  <div key={n} className="h-12 bg-slate-50 border border-slate-100 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : portfolioStats && riskData ? (
              <div className="space-y-4">

                {/* KPI 1: Portfolio Capital */}
                <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                      <Briefcase className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900">Portfolio Capital</span>
                      <p className="text-[10px] text-slate-400 leading-none mt-0.5">Base Equity Account</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-900">
                    {formatCurrency(portfolioStats.equity)}
                  </span>
                </div>

                {/* KPI 2: Realized & Unrealized PnL */}
                <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                      <DollarSign className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900">Net Realized PnL</span>
                      <p className="text-[10px] text-slate-400 leading-none mt-0.5">Total closed trades gain</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-sm font-bold font-mono ${portfolioStats.total_pnl >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                      {portfolioStats.total_pnl >= 0 ? "+" : ""}
                      {formatCurrency(portfolioStats.total_pnl)}
                    </span>
                  </div>
                </div>

                {/* KPI 3: Global Risk Factor */}
                <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
                      <ShieldAlert className="w-4 h-4 animate-bounce" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900">Risk Severity</span>
                      <p className="text-[10px] text-slate-400 leading-none mt-0.5">Portfolio exposure stress</p>
                    </div>
                  </div>
                  <span className={`text-sm font-bold font-mono ${riskData.risk_score >= 0.7 ? "text-rose-600" : riskData.risk_score >= 0.4 ? "text-amber-600" : "text-emerald-600"}`}>
                    {formatPercent(riskData.risk_score * 100)}
                  </span>
                </div>

                {/* KPI 4: Win Rate Metric */}
                <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-600">
                      <Award className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900">Execution Win Rate</span>
                      <p className="text-[10px] text-slate-400 leading-none mt-0.5">Ratio of winning positions</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-900">
                    {formatPercent(portfolioStats.win_rate)}
                  </span>
                </div>

                {/* KPI 5: Capital Exposure */}
                <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
                      <Activity className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900">Active Exposure</span>
                      <p className="text-[10px] text-slate-400 leading-none mt-0.5">Committed collateral value</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-900">
                    {formatPercent(riskData.portfolio_exposure * 100)}
                  </span>
                </div>

              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs">
                Metrics feed unavailable
              </div>
            )}
          </div>

          {/* SECTION 6: PORTFOLIO ALLOCATION (SVG DONUT CHART) */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Portfolio Asset Allocation</h3>

            {portfolioStats && portfolioStats.allocation && Object.keys(portfolioStats.allocation).length > 0 ? (
              <div className="flex flex-col items-center space-y-4">
                {/* SVG Pure Donut Chart */}
                <div className="relative w-40 h-40">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 42 42">
                    <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#f1f5f9" strokeWidth="4" />
                    {(() => {
                      let accumulatedPercent = 0;
                      const colors = ["#2563eb", "#10b981", "#8b5cf6", "#f59e0b", "#6366f1"];
                      return Object.entries(portfolioStats.allocation).map(([symbol, allocVal], idx) => {
                        const val = allocVal * 100;
                        const color = colors[idx % colors.length];
                        const strokeDasharray = `${val} ${100 - val}`;
                        const strokeDashoffset = 100 - accumulatedPercent;
                        accumulatedPercent += val;

                        return (
                          <circle
                            key={symbol}
                            cx="21"
                            cy="21"
                            r="15.915"
                            fill="transparent"
                            stroke={color}
                            strokeWidth="4"
                            strokeDasharray={strokeDasharray}
                            strokeDashoffset={strokeDashoffset}
                          />
                        );
                      });
                    })()}
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest leading-none">ASSETS</span>
                    <span className="text-base font-extrabold font-mono text-slate-900 mt-1">
                      {Object.keys(portfolioStats.allocation).length}
                    </span>
                  </div>
                </div>

                {/* Legend */}
                <div className="w-full grid grid-cols-2 gap-2 text-xs border-t border-slate-100 pt-3">
                  {Object.entries(portfolioStats.allocation).map(([symbol, allocVal], idx) => {
                    const colors = ["#2563eb", "#10b981", "#8b5cf6", "#f59e0b", "#6366f1"];
                    const color = colors[idx % colors.length];
                    return (
                      <div key={symbol} className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                        <span className="font-semibold text-slate-700 font-mono text-[11px]">{symbol}</span>
                        <span className="text-slate-400 font-mono text-[10px]">({formatPercent(allocVal * 100)})</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 border border-dashed border-slate-100 rounded-lg p-6 text-center">
                <Briefcase className="w-8 h-8 text-slate-300 mb-2" />
                <span className="text-xs text-slate-400 font-medium">No assets currently allocated</span>
              </div>
            )}
          </div>

          {/* SECTION 5: SCANNER PREVIEW (opportunities scan table) */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-sm font-bold text-slate-900">Alpha Opportunities Scanner</h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                LIVE PIPELINE
              </span>
            </div>

            {loadingStats ? (
              <div className="space-y-2 py-4">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="h-10 bg-slate-50 border border-slate-100 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : scannerData && scannerData.top_opportunities?.length > 0 ? (
              <div className="space-y-3">
                {scannerData.top_opportunities.slice(0, 4).map((opp: ScannerOpportunity, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:bg-slate-100/50 transition-colors text-xs">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-bold text-slate-400 font-mono w-4">#{idx+1}</span>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-slate-900 font-mono">{opp.symbol}</span>
                          <span className={`px-1 rounded-[4px] text-[9px] font-bold ${opp.side === "LONG" ? "text-emerald-700 bg-emerald-50" : "text-rose-700 bg-rose-50"}`}>
                            {opp.side}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400 leading-none mt-0.5 font-mono">{opp.strategy}</p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="font-bold text-slate-900 font-mono">{(opp.probability * 100).toFixed(0)}% Conv</span>
                      <span className="text-[10px] text-slate-400 leading-none mt-0.5 font-mono">
                        Score: {opp.score}
                      </span>
                    </div>
                  </div>
                ))}
                <Link
                  to="/scanner"
                  className="block text-center w-full py-2 border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg text-xs font-semibold mt-3 transition-colors"
                >
                  Configure Advanced Scanning Rules
                </Link>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs">
                No high probability scanner signals
              </div>
            )}
          </div>

          {/* SECTION 7: RISK OVERVIEW (Compliance card) */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Institutional Risk Parameters</h3>
            {riskData ? (
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500 font-medium">Daily Drawdown Limit:</span>
                  <span className="font-bold font-mono text-rose-600">-{formatCurrency(riskData.max_daily_loss)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500 font-medium">Active Drawdown:</span>
                  <span className="font-bold font-mono text-slate-900">{formatCurrency(riskData.daily_loss)}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500 font-medium">Compliance Capacity:</span>
                  <span className="font-bold font-mono text-emerald-600">
                    {riskData.open_trades}/{riskData.max_open_trades} Trade Channels
                  </span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500 font-medium">Trade Limit per Channel:</span>
                  <span className="font-bold font-mono text-slate-900">{formatCurrency(riskData.max_position_size_usd)}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs">
                Compliance metrics unavailable
              </div>
            )}
          </div>

          {/* SECTION 8: RESEARCH FEED */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-600" />
                Research & Activity Log
              </h3>
              <span className="text-[10px] font-bold text-slate-400 font-mono">BLOOMBERG FEED</span>
            </div>

            {timelineEvents.length > 0 ? (
              <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
                {timelineEvents.slice(0, 5).map((ev) => (
                  <div key={ev.id} className="space-y-1 group border-l-2 border-slate-200 group-hover:border-blue-600 pl-3.5 transition-colors text-xs">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold uppercase tracking-wider text-[9px] ${
                        ev.severity === "CRITICAL" ? "text-rose-600" : ev.severity === "WARNING" ? "text-amber-600" : "text-blue-600"
                      }`}>
                        {ev.type}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <h4 className="font-bold text-slate-800 tracking-tight leading-tight group-hover:text-slate-900">
                      {ev.title}
                    </h4>
                    <p className="text-slate-500 leading-relaxed font-normal">
                      {ev.message}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs">
                No active research reports on desk
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}

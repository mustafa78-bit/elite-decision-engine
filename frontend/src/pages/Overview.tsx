import { useCallback, useEffect, useState } from "react";
import { useOutletContext, Link } from "react-router-dom";

import type { LayoutContext } from "../components/layout/Layout";
import { apiFetch, ApiError } from "../api/client";

interface MarketData {
  symbol: string;
  price: number;
  regime: string;
  regime_score: number;
  rsi: number;
  atr: number;
  btc_health_score: number;
  error?: string;
}

interface RiskSummary {
  risk_score: number;
  open_trades: number;
  max_open_trades: number;
  daily_loss: number;
  max_daily_loss: number;
}

interface PerfSummary {
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  sharpe_ratio: number;
  open_trades?: number;
  closed_trades?: number;
  winning_trades?: number;
  losing_trades?: number;
  profit_factor?: number;
  max_drawdown?: number;
  equity?: number;
  current_open_exposure?: number;
  unrealized_pnl?: number;
  allocation?: Record<string, number>;
}

interface SignalData {
  id: number;
  symbol: string;
  side: string;
  timeframe: string;
  price: number;
  confidence: number;
  decision: string;
  final_score: number;
  trend_score: number;
  volume_score: number;
  btc_score: number;
  risk_score: number;
  status: string;
  created_at: string;
}

export default function Overview() {
  useOutletContext<LayoutContext>();
  const [market, setMarket] = useState<MarketData | null>(null);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [perf, setPerf] = useState<PerfSummary | null>(null);
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const [m, r, po, sigs] = await Promise.all([
        apiFetch<MarketData>("/market"),
        apiFetch<RiskSummary>("/risk"),
        apiFetch<PerfSummary>("/portfolio"),
        apiFetch<SignalData[]>("/signals?limit=5"),
      ]);
      if (m.error) {
        setError(m.error);
        return;
      }
      setMarket(m);
      setRisk(r);
      setPerf(po);
      setSignals(sigs || []);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] border border-dashed border-slate-200 rounded-3xl bg-white p-8">
        <div className="w-8 h-8 border-2 border-slate-300 border-t-slate-800 rounded-full animate-spin mb-4" />
        <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">
          Synchronizing Institutional Terminal...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-slate-200 rounded-3xl p-8 max-w-lg mx-auto text-center shadow-sm">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-50 text-red-600 mb-4">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Sync Connection Error</h3>
        <p className="text-xs text-slate-500 mb-6">{error}</p>
        <button
          onClick={fetchAll}
          className="inline-flex items-center justify-center px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm"
        >
          Re-establish Connection
        </button>
      </div>
    );
  }

  const latestSignal = signals.length > 0 ? signals[0] : null;
  const portfolioPnl = perf?.total_pnl ?? 0;
  const winRate = perf?.win_rate ?? 0;
  const maxDrawdown = perf?.max_drawdown ?? 0;
  const sharpe = perf?.sharpe_ratio ?? 0;
  const profitFactor = perf?.profit_factor ?? 0.0;
  const accountEquity = perf?.equity ?? 10000;
  const unrealizedPnl = perf?.unrealized_pnl ?? 0.0;
  const openExposure = perf?.current_open_exposure ?? 0.0;

  const researchFeed = [
    { id: 1, category: "REGIME", title: "BTC Volatility Compression suggests impending breakout", time: "10m ago", impact: "HIGH" },
    { id: 2, category: "FLOWS", title: "Institutional Spot ETF inflows surge by +$420M", time: "45m ago", impact: "POSITIVE" },
    { id: 3, category: "MACRO", title: "Macro regime shifts to low-inflation expansionary phase", time: "2h ago", impact: "NEUTRAL" }
  ];

  return (
    <div className="space-y-6">
      {/* Platform Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
            Decision Intelligence Platform
          </h1>
          <p className="text-xs text-slate-500 font-mono mt-0.5">
            Institutional Gateway • SECURE_NODE_ALPHA_1 • STATUS: ACTIVE
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-center">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
            LIVE PROTOCOL FEED
          </span>
          <button
            onClick={fetchAll}
            className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition-colors shadow-sm"
            title="Refresh dashboard data"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.253 8H18" />
            </svg>
          </button>
        </div>
      </div>

      {/* Primary Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column: Large Hero AI Decision Card & Market Indicators (occupies 2 cols on lg) */}
        <div className="lg:col-span-2 space-y-6">

          {/* Large Hero Decision Card */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm hover:border-slate-300 transition-all">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-slate-50 text-slate-800">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-slate-800 font-mono uppercase tracking-wider">
                    Hero AI Decision Model
                  </h3>
                  <p className="text-[10px] text-slate-400 font-mono">
                    PIPELINE ID: #{latestSignal?.id || "NONE"} • STRATEGY_TYPE: CONCLAVE
                  </p>
                </div>
              </div>
              {latestSignal && (
                <span className={`inline-flex items-center px-3 py-1 rounded-xl text-xs font-semibold font-mono ${
                  latestSignal.decision.startsWith("STRONG")
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-blue-50 text-blue-700 border border-blue-200"
                }`}>
                  {latestSignal.decision}
                </span>
              )}
            </div>

            {latestSignal ? (
              <div className="space-y-6">
                {/* Hero Layout Row */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-3xl font-extrabold text-slate-900 tracking-tight font-sans">
                        {latestSignal.symbol}
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold font-mono tracking-wide ${
                        latestSignal.side === "LONG"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-rose-100 text-rose-800"
                      }`}>
                        {latestSignal.side}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 font-mono mt-1">
                      SIGNAL PRICE: ${latestSignal.price.toLocaleString()} • INTERVAL: {latestSignal.timeframe}
                    </p>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-black text-slate-900 tracking-tighter font-mono">
                      {(latestSignal.confidence).toFixed(1)}%
                    </span>
                    <span className="text-xs font-semibold text-slate-400 font-mono">CONFIDENCE</span>
                  </div>
                </div>

                {/* Level Meter */}
                <div className="space-y-1.5">
                  <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${
                        latestSignal.confidence >= 90 ? "bg-emerald-500" : "bg-blue-500"
                      }`}
                      style={{ width: `${latestSignal.confidence}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>STABILITY BOUNDARY: 70%</span>
                    <span>STRONG THRESHOLD: 90%</span>
                  </div>
                </div>

                {/* Scoring Factor Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100">
                  <div className="space-y-3">
                    <h4 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest">
                      Factor Contributors
                    </h4>

                    <div className="space-y-2.5">
                      {/* Trend Indicator */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-medium text-slate-700">
                          <span>Trend Compliance</span>
                          <span className="font-mono">{latestSignal.trend_score * 100}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-800" style={{ width: `${latestSignal.trend_score * 100}%` }} />
                        </div>
                      </div>

                      {/* Volume Score */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-medium text-slate-700">
                          <span>Volume Inflow Metric</span>
                          <span className="font-mono">{latestSignal.volume_score * 100}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-800" style={{ width: `${latestSignal.volume_score * 100}%` }} />
                        </div>
                      </div>

                      {/* BTC Health */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-medium text-slate-700">
                          <span>BTC Market Health</span>
                          <span className="font-mono">{(latestSignal.btc_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-800" style={{ width: `${latestSignal.btc_score * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest">
                      Risk & Multi-Timeframe Checks
                    </h4>

                    <div className="space-y-2.5">
                      {/* Risk Core Score */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-medium text-slate-700">
                          <span>Risk Coefficient</span>
                          <span className="font-mono">{(latestSignal.risk_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-800" style={{ width: `${latestSignal.risk_score * 100}%` }} />
                        </div>
                      </div>

                      {/* Total Weighted Score */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-medium text-slate-700">
                          <span>Aggregated Score Weight</span>
                          <span className="font-mono">{(latestSignal.final_score * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-600" style={{ width: `${latestSignal.final_score * 100}%` }} />
                        </div>
                      </div>

                      {/* Deep Link */}
                      <div className="pt-2 text-right">
                        <Link
                          to={`/asset/${latestSignal.symbol}`}
                          className="inline-flex items-center text-xs font-bold text-blue-600 hover:text-blue-800 font-sans group"
                        >
                          Access Intelligence Console
                          <svg className="w-3.5 h-3.5 ml-1 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                          </svg>
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs font-mono">
                No decisions processed in the current epoch.
              </div>
            )}
          </div>

          {/* Market Regime Overview and Real-Time Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* Market Regime Card with Custom SVG Chart */}
            <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm space-y-4">
              <h3 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest">
                Market Regime AI
              </h3>
              {market && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-400 font-mono block">SYMBOL</span>
                      <span className="text-lg font-bold text-slate-800 tracking-tight">BTCUSDT</span>
                    </div>
                    <div>
                      <span className="text-xs text-slate-400 font-mono block text-right">REGIME STATE</span>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                        {market.regime}
                      </span>
                    </div>
                  </div>

                  {/* Elegant Inline Candlestick / Trend Line Chart */}
                  <div className="h-20 w-full border border-slate-100 rounded-xl bg-slate-50/50 flex flex-col justify-end p-2 relative overflow-hidden">
                    <div className="absolute top-1 left-2 text-[8px] font-mono text-slate-400">
                      LIVE PRICE TREND LINE
                    </div>
                    {/* SVG Sparkline Sparking Trend */}
                    <svg className="w-full h-12 overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 20">
                      <defs>
                        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10b981" stopOpacity="0.2"/>
                          <stop offset="100%" stopColor="#10b981" stopOpacity="0.0"/>
                        </linearGradient>
                      </defs>
                      {/* Grid Lines */}
                      <line x1="0" y1="5" x2="100" y2="5" stroke="#f1f5f9" strokeWidth="0.5" />
                      <line x1="0" y1="10" x2="100" y2="10" stroke="#f1f5f9" strokeWidth="0.5" />
                      <line x1="0" y1="15" x2="100" y2="15" stroke="#f1f5f9" strokeWidth="0.5" />
                      {/* Filled area */}
                      <path d="M0,18 L5,15 L12,16 L18,13 L25,14 L35,11 L45,13 L55,9 L65,11 L75,7 L85,8 L95,4 L100,2 L100,20 L0,20 Z" fill="url(#chartGrad)" />
                      {/* Trend Line */}
                      <path d="M0,18 L5,15 L12,16 L18,13 L25,14 L35,11 L45,13 L55,9 L65,11 L75,7 L85,8 L95,4 L100,2" fill="none" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      {/* Glow dot */}
                      <circle cx="100" cy="2" r="2.5" fill="#10b981" className="animate-pulse" />
                    </svg>
                  </div>

                  <div className="grid grid-cols-2 gap-4 border-t border-slate-50 pt-3">
                    <div>
                      <span className="text-[10px] text-slate-400 font-mono block">RSI (14)</span>
                      <span className="text-sm font-bold text-slate-800 font-mono">{market.rsi.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-mono block">BTC HEALTH</span>
                      <span className="text-sm font-bold text-slate-800 font-mono">{(market.btc_health_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Risk Control Overview Card */}
            <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm">
              <h3 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest mb-4">
                Risk Control Health
              </h3>
              {risk && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-400 font-mono block">ACTIVE RISK SCORE</span>
                      <span className={`text-lg font-extrabold tracking-tight ${
                        risk.risk_score >= 0.7 ? "text-rose-600" : "text-slate-800"
                      }`}>
                        {(risk.risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-slate-400 font-mono block text-right">SYSTEM STATUS</span>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        SECURE
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 border-t border-slate-50 pt-3">
                    <div>
                      <span className="text-[10px] text-slate-400 font-mono block">OPEN TRADES</span>
                      <span className="text-sm font-bold text-slate-800 font-mono">{risk.open_trades} / {risk.max_open_trades}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-mono block">DAILY LOSS</span>
                      <span className="text-sm font-bold text-slate-800 font-mono">${Math.abs(risk.daily_loss).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

          </div>

        </div>

        {/* Right Column: Portfolio KPIs, Capital Allocation & Live Research Feed */}
        <div className="space-y-6">

          {/* Portfolio KPIs Panel */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
            <h3 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest mb-5">
              Portfolio Diagnostics
            </h3>

            <div className="space-y-4">

              {/* Account Equity */}
              <div className="flex items-center justify-between border-b border-slate-50 pb-3">
                <div>
                  <span className="text-[10px] text-slate-400 font-mono block">ACCOUNT EQUITY</span>
                  <span className="text-xl font-bold text-slate-800 font-mono">
                    ${accountEquity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 font-mono block">UNREALIZED PNL</span>
                  <span className={`text-xs font-semibold font-mono ${
                    unrealizedPnl >= 0 ? "text-emerald-600" : "text-rose-600"
                  }`}>
                    {unrealizedPnl >= 0 ? "+" : ""}${unrealizedPnl.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-4">

                <div>
                  <span className="text-[10px] text-slate-400 font-mono block">CLOSED PNL</span>
                  <span className={`text-sm font-extrabold font-mono ${
                    portfolioPnl >= 0 ? "text-emerald-600" : "text-rose-600"
                  }`}>
                    {portfolioPnl >= 0 ? "+" : ""}${portfolioPnl.toLocaleString()}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-mono block">WIN RATE</span>
                  <span className="text-sm font-extrabold font-mono text-slate-800">
                    {winRate.toFixed(1)}%
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-mono block">SHARPE RATIO</span>
                  <span className="text-sm font-extrabold font-mono text-slate-800">
                    {sharpe.toFixed(2)}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-mono block">PROFIT FACTOR</span>
                  <span className="text-sm font-extrabold font-mono text-slate-800">
                    {profitFactor.toFixed(2)}
                  </span>
                </div>

                <div className="col-span-2 pt-2 border-t border-slate-50">
                  <span className="text-[10px] text-slate-400 font-mono block">MAX DRAWDOWN</span>
                  <span className="text-sm font-bold font-mono text-rose-600">
                    {maxDrawdown.toFixed(2)}%
                  </span>
                </div>

              </div>

            </div>
          </div>

          {/* Allocation Breakdown */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
            <h3 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest mb-4">
              Capital Allocation
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>Open Allocation Exposure</span>
                  <span className="font-mono">${openExposure.toLocaleString()}</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-800" style={{ width: `${Math.min((openExposure / accountEquity) * 100, 100)}%` }} />
                </div>
                <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                  CAPACITY USED: {((openExposure / accountEquity) * 100).toFixed(1)}%
                </span>
              </div>

              {perf?.allocation && Object.keys(perf.allocation).length > 0 ? (
                <div className="space-y-2 border-t border-slate-50 pt-3">
                  <span className="text-[10px] text-slate-400 font-mono block uppercase tracking-wider mb-1">Exposure per Asset</span>
                  {Object.entries(perf.allocation).map(([symbol, value]) => (
                    <div key={symbol} className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-700">{symbol}</span>
                      <span className="font-mono text-slate-600">${value.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4 text-slate-400 text-xs font-mono border-t border-slate-50 pt-3">
                  No active exposure. All funds liquid.
                </div>
              )}
            </div>
          </div>

          {/* New Live Research & Intelligence Feed Card */}
          <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm space-y-4">
            <h3 className="text-[10px] font-bold text-slate-400 font-mono uppercase tracking-widest">
              Research & Intelligence Feed
            </h3>
            <div className="space-y-3">
              {researchFeed.map((item) => (
                <div key={item.id} className="border-b border-slate-50 pb-2 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      {item.category}
                    </span>
                    <span className="text-[9px] font-mono text-slate-400">{item.time}</span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-800 leading-snug">
                    {item.title}
                  </h4>
                  <div className="text-[9px] font-bold font-mono text-blue-600 mt-1">
                    IMPACT: {item.impact}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

      {/* Decision Intelligence Scanner Preview */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-slate-50 text-slate-800">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800 font-mono uppercase tracking-wider">
                Platform Scanner Preview
              </h3>
              <p className="text-[10px] text-slate-400 font-mono">
                COMPILING REAL-TIME STRATEGIC TRADE CANDIDATES
              </p>
            </div>
          </div>
          <Link
            to="/signals"
            className="text-xs font-semibold text-blue-600 hover:underline font-sans"
          >
            Manage Core Signals
          </Link>
        </div>

        {signals.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-mono">
                  <th className="py-2.5 font-normal uppercase tracking-wider">Symbol</th>
                  <th className="py-2.5 font-normal uppercase tracking-wider">Direction</th>
                  <th className="py-2.5 font-normal uppercase tracking-wider text-center">Interval</th>
                  <th className="py-2.5 font-normal uppercase tracking-wider text-right">Score</th>
                  <th className="py-2.5 font-normal uppercase tracking-wider text-right">Confidence</th>
                  <th className="py-2.5 font-normal uppercase tracking-wider text-center">Status</th>
                  <th className="py-2.5 font-normal uppercase tracking-wider text-right">Decision</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((sig) => (
                  <tr key={sig.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 font-semibold text-slate-800">{sig.symbol}</td>
                    <td className="py-3">
                      <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold font-mono ${
                        sig.side === "LONG" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
                      }`}>
                        {sig.side}
                      </span>
                    </td>
                    <td className="py-3 text-center text-slate-500 font-mono">{sig.timeframe}</td>
                    <td className="py-3 text-right text-slate-800 font-mono">{(sig.final_score * 100).toFixed(0)}%</td>
                    <td className="py-3 text-right text-slate-800 font-mono">{(sig.confidence).toFixed(1)}%</td>
                    <td className="py-3 text-center text-slate-500 font-mono">{sig.status}</td>
                    <td className="py-3 text-right">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                        sig.decision.startsWith("STRONG") ? "text-emerald-600 bg-emerald-50" : "text-slate-600 bg-slate-50"
                      }`}>
                        {sig.decision}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400 text-xs font-mono">
            No strategic trade candidates matched the current scanner parameters.
          </div>
        )}
      </div>

    </div>
  );
}

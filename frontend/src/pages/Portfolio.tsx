import { useCallback, useEffect, useState } from "react";
import { useOutletContext, Link } from "react-router-dom";
import {
  ShieldAlert,
  PieChart,
  Activity,
  RefreshCw,
  Zap,
  AlertTriangle,
  PlusCircle,
  Compass,
  Grid3X3,
  ArrowRight,
  FileText
} from "lucide-react";

import type { LayoutContext } from "../components/layout/Layout";
import type { PortfolioStats } from "../api/portfolio";
import { fetchPortfolio } from "../api/portfolio";
import { fetchPortfolioFull } from "../api/portfolio_detail";
import type { PortfolioFullDTO, PortfolioAdvisorDTO } from "../types/api/portfolio";
import { ApiError } from "../api/client";
import BalanceCard from "../components/portfolio/BalanceCard";
import PositionTable from "../components/portfolio/PositionTable";
import MetricCard from "../components/MetricCard";

export default function Portfolio() {
  const { openTrades } = useOutletContext<LayoutContext>();
  const [port, setPort] = useState<PortfolioStats | null>(null);
  const [fullPort, setFullPort] = useState<PortfolioFullDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Interactive Stress-test multiplier slider
  const [simulationShock, setSimulationShock] = useState<number>(1.0); // 1.0x standard multiplier

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const [portData, fullData] = await Promise.all([
        fetchPortfolio(),
        fetchPortfolioFull()
      ]);
      setPort(portData);
      setFullPort(fullData);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4 border border-dashed border-[var(--border-subtle)] rounded bg-[var(--background-card)]">
        <div className="w-8 h-8 border-4 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin"></div>
        <div className="text-[var(--text-secondary)] text-xs font-mono animate-pulse">
          OLLO IS GENERATING AI ADVISORY DISPATCH...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)] bg-[var(--accent-red)]/10 rounded font-mono">
          [ERROR] {error}
          <button onClick={load} className="ml-4 underline text-white hover:text-[var(--accent-blue)] font-bold">
            RETRY DIAGNOSTIC SCAN
          </button>
        </div>
      </div>
    );
  }

  if (!port || !fullPort) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center font-mono">
        PORTFOLIO INTEL TIMED OUT
      </div>
    );
  }

  const advisor: PortfolioAdvisorDTO = fullPort.advisor || {
    health_score: 100,
    health_deductions: [],
    diversification: {
      concentration_ratio: 0.0,
      status: "DIVERSIFIED",
      message: "No open positions. Portfolio is 100% Cash."
    },
    sector_exposure: [],
    correlation_matrix: [],
    risk: { score: 1.0, label: "CONSERVATIVE" },
    worst_case_scenarios: [],
    rebalancing_suggestions: [],
    opportunity_recommendations: []
  };

  const executiveSummary = advisor.executive_summary || {
    overall_health_score: advisor.health_score,
    current_risk_level: advisor.risk.label,
    biggest_weakness: "None Detected",
    biggest_opportunity: "Deploy Cash Reserves",
    recommended_action: "Deploy Cash Reserves into BTCUSDT and ETHUSDT core positions.",
    conclusions: {
      health: "MONITOR",
      diversification: "DIVERSIFY",
      stress_testing: "MONITOR"
    }
  };

  const positions = openTrades.map((t) => ({
    symbol: t.symbol,
    side: t.side,
    entry: t.entry,
    status: t.status,
    pnl: t.pnl,
  }));

  // Style helpers
  const getHealthColor = (score: number) => {
    if (score >= 80) return "text-[var(--accent-green)] border-[var(--accent-green)]";
    if (score >= 50) return "text-[var(--accent-yellow)] border-[var(--accent-yellow)]";
    return "text-[var(--accent-red)] border-[var(--accent-red)]";
  };

  const getHealthBg = (score: number) => {
    if (score >= 80) return "bg-[var(--accent-green)]/10";
    if (score >= 50) return "bg-[var(--accent-yellow)]/10";
    return "bg-[var(--accent-red)]/10";
  };

  const getConclusionBadge = (conclusion: string) => {
    switch (conclusion) {
      case "TRIM":
      case "REDUCE":
      case "HEDGE":
        return "bg-[var(--accent-red)]/10 text-[var(--accent-red)] border-[var(--accent-red)]/30";
      case "REBALANCE":
      case "DIVERSIFY":
        return "bg-[var(--accent-yellow)]/10 text-[var(--accent-yellow)] border-[var(--accent-yellow)]/30";
      default:
        return "bg-[var(--accent-green)]/10 text-[var(--accent-green)] border-[var(--accent-green)]/30";
    }
  };

  return (
    <div className="space-y-6">

      {/* 1. EXECUTIVE SUMMARY WORKSPACE (Highest Priority #1) */}
      <div className="border-2 border-[var(--accent-blue)] rounded bg-[var(--background-card)] overflow-hidden shadow-lg">
        <div className="bg-[var(--accent-blue)]/15 px-4 py-3 border-b border-[var(--accent-blue)]/30 flex items-center justify-between">
          <span className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2">
            <Activity className="w-4 h-4 animate-pulse text-[var(--accent-blue)]" />
            WHAT SHOULD I CHANGE IN MY PORTFOLIO TODAY?
          </span>
          <span className="text-[10px] font-mono text-[var(--accent-blue)] font-bold uppercase tracking-wider">OLLO REAL-TIME RECOMMENDATION</span>
        </div>
        <div className="p-5 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">IMMEDIATE AI RECOMMENDED ACTION</span>
              <p className="text-lg font-bold text-white font-mono flex items-center gap-2">
                <ArrowRight className="w-5 h-5 text-[var(--accent-blue)] shrink-0 animate-bounce" />
                {executiveSummary.recommended_action}
              </p>
            </div>
            <div className="shrink-0 flex items-center gap-2">
              <button
                onClick={() => {
                  const el = document.getElementById("rebalancing-suggestions");
                  el?.scrollIntoView({ behavior: "smooth" });
                }}
                className="px-4 py-2 text-xs font-mono font-bold bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/80 text-white uppercase tracking-wider rounded transition-all flex items-center gap-2"
              >
                EXECUTE ADVISORY <Zap className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
            <div className="p-3 bg-[var(--border-subtle)]/30 rounded border border-[var(--border-subtle)]/50">
              <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-widest">PORTFOLIO HEALTH</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className={`text-xl font-bold font-mono ${getHealthColor(executiveSummary.overall_health_score)}`}>
                  {executiveSummary.overall_health_score}/100
                </span>
              </div>
            </div>
            <div className="p-3 bg-[var(--border-subtle)]/30 rounded border border-[var(--border-subtle)]/50">
              <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-widest">CURRENT RISK PROFILE</span>
              <p className="text-sm font-bold font-mono text-white mt-1 uppercase tracking-tight">
                {executiveSummary.current_risk_level}
              </p>
            </div>
            <div className="p-3 bg-[var(--border-subtle)]/30 rounded border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/5">
              <span className="text-[9px] font-mono text-[var(--accent-red)] uppercase tracking-widest font-bold">CRITICAL WEAKNESS</span>
              <p className="text-xs font-bold text-white font-mono mt-1 overflow-hidden text-ellipsis whitespace-nowrap">
                {executiveSummary.biggest_weakness}
              </p>
            </div>
            <div className="p-3 bg-[var(--border-subtle)]/30 rounded border border-[var(--accent-green)]/20 bg-[var(--accent-green)]/5">
              <span className="text-[9px] font-mono text-[var(--accent-green)] uppercase tracking-widest font-bold">TOP ALPHA SETUP</span>
              <p className="text-xs font-bold text-white font-mono mt-1 overflow-hidden text-ellipsis whitespace-nowrap">
                {executiveSummary.biggest_opportunity}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. REBALANCING SUGGESTIONS PANEL WITH EXPLICIT WHY/EVIDENCE (Product Review Priority #2, #4) */}
      <div id="rebalancing-suggestions" className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)] scroll-mt-6">
        <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)] flex items-center justify-between">
          <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-[var(--accent-blue)]" />
            AI ADVISORY: REBALANCING STRATEGIES
          </span>
          <span className="text-[10px] font-mono text-[var(--accent-green)] font-bold">ACTION REQUIRED</span>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {advisor.rebalancing_suggestions.map((sug, idx) => (
              <div key={idx} className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)] flex flex-col justify-between overflow-hidden">
                <div className="p-4 space-y-3.5">
                  <div className="flex justify-between items-center border-b border-[var(--border-subtle)] pb-2.5">
                    <span className="text-sm font-bold text-white font-mono tracking-tight">{sug.symbol}</span>
                    <span className={`text-[10px] font-mono font-bold tracking-widest px-2.5 py-0.5 rounded border ${
                      sug.action === "TRIM" ? "bg-[var(--accent-red)]/10 text-[var(--accent-red)] border-[var(--accent-red)]/20" : "bg-[var(--accent-green)]/10 text-[var(--accent-green)] border-[var(--accent-green)]/20"
                    }`}>
                      {sug.action} ${sug.amount.toLocaleString()} ({sug.percentage}%)
                    </span>
                  </div>

                  {/* Structured Explanation (Q&A - Product Review Priority #4) */}
                  <div className="space-y-2 text-xs font-mono">
                    <div>
                      <span className="text-[10px] font-bold text-[var(--accent-blue)] uppercase block mb-0.5">WHY:</span>
                      <p className="text-white leading-relaxed font-sans">{sug.why || sug.reason}</p>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-[var(--accent-yellow)] uppercase block mb-0.5">EVIDENCE SUPPORT:</span>
                      <p className="text-[var(--text-muted)] leading-relaxed font-sans">{sug.evidence || "Portfolio exposure variance thresholds tripped."}</p>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-[var(--accent-green)] uppercase block mb-0.5">EXPECTED BENEFIT:</span>
                      <p className="text-[var(--text-muted)] leading-relaxed font-sans">{sug.expected_benefit || "Optimizes risk-adjusted Sharpe/Sortino ratios."}</p>
                    </div>
                  </div>
                </div>
                <div className="bg-[var(--border-subtle)]/20 px-4 py-2 border-t border-[var(--border-subtle)] flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">REBALANCING ACTION CONCLUSION</span>
                  <button className="text-xs font-mono font-bold uppercase text-[var(--accent-blue)] hover:underline flex items-center gap-1">
                    EXECUTE ORDER <Zap className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. HEALTH & RISK DIAGNOSTICS WITH CONCLUSIONS (Product Review Priority #2, #3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Health Diagnostic Panel */}
        <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)] overflow-hidden flex flex-col justify-between">
          <div>
            <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Compass className="w-4 h-4 text-[var(--accent-blue)]" />
                HEALTH DIAGNOSTIC SUMMARY
              </span>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex items-center gap-4">
                <div className={`w-16 h-16 rounded-full border-4 flex flex-col items-center justify-center shrink-0 ${getHealthColor(advisor.health_score)} ${getHealthBg(advisor.health_score)}`}>
                  <span className="text-xl font-bold font-mono leading-none">{advisor.health_score}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">DIAGNOSTIC STATUS</span>
                  <p className="text-xs font-bold text-white font-sans uppercase">
                    {advisor.health_score >= 80 ? "Nominal Operations" : (advisor.health_score >= 50 ? "Action Recommended" : "Critical Risk Event")}
                  </p>
                </div>
              </div>

              <div className="space-y-1.5 max-h-40 overflow-y-auto">
                {advisor.health_deductions.map((ded, idx) => (
                  <div key={idx} className="flex items-start gap-1.5 text-[11px] font-mono text-white bg-[var(--accent-red)]/5 border-l-2 border-[var(--accent-red)] p-1.5 rounded-r">
                    <AlertTriangle className="w-3.5 h-3.5 text-[var(--accent-red)] shrink-0 mt-0.5" />
                    <span>{ded}</span>
                  </div>
                ))}
                {advisor.health_deductions.length === 0 && (
                  <p className="text-xs text-[var(--accent-green)] font-mono">No active deductions. Portfolio aligns with institutional benchmarks.</p>
                )}
              </div>
            </div>
          </div>

          {/* ACTION CONCLUSION Badges */}
          <div className="bg-[var(--border-subtle)]/20 px-4 py-2.5 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="text-[10px] font-mono text-[var(--text-muted)]">AI DECISION CONCLUSION:</span>
            <span className={`text-[10px] font-mono font-bold tracking-widest px-2.5 py-1 rounded border uppercase ${getConclusionBadge(executiveSummary.conclusions.health)}`}>
              {executiveSummary.conclusions.health}
            </span>
          </div>
        </div>

        {/* Diversification & Concentration Panel */}
        <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)] overflow-hidden flex flex-col justify-between">
          <div>
            <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <PieChart className="w-4 h-4 text-[var(--accent-blue)]" />
                CONCENTRATION & SECTOR DIAGNOSTICS
              </span>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex justify-between items-center border-b border-[var(--border-subtle)]pb-2">
                <div>
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">HIGHEST CONCENTRATION</span>
                  <span className="text-sm font-bold font-mono text-white">
                    {advisor.diversification.concentration_ratio > 0 ? `${(advisor.diversification.concentration_ratio * 100).toFixed(1)}%` : "0.0%"}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">STATUS</span>
                  <span className={`text-[10px] font-mono font-bold tracking-widest px-2 py-0.5 rounded border ${
                    advisor.diversification.status === "CONCENTRATED" ? "bg-[var(--accent-red)]/10 text-[var(--accent-red)] border-[var(--accent-red)]/20" : "bg-[var(--accent-green)]/10 text-[var(--accent-green)] border-[var(--accent-green)]/20"
                  }`}>
                    {advisor.diversification.status}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">SECTOR ALLOCATION OVERVIEW:</span>
                <div className="space-y-1.5 max-h-36 overflow-y-auto">
                  {advisor.sector_exposure.map((exp, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs font-mono">
                      <span className="text-white font-bold">{exp.sector}</span>
                      <span className="text-[var(--text-muted)]">{exp.percentage}%</span>
                    </div>
                  ))}
                  {advisor.sector_exposure.length === 0 && (
                    <p className="text-xs text-[var(--text-muted)] font-mono">No active exposures. Portfolio resides completely in dry powder fiat cash.</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ACTION CONCLUSION Badges */}
          <div className="bg-[var(--border-subtle)]/20 px-4 py-2.5 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="text-[10px] font-mono text-[var(--text-muted)]">AI DECISION CONCLUSION:</span>
            <span className={`text-[10px] font-mono font-bold tracking-widest px-2.5 py-1 rounded border uppercase ${getConclusionBadge(executiveSummary.conclusions.diversification)}`}>
              {executiveSummary.conclusions.diversification}
            </span>
          </div>
        </div>

        {/* Stress Testing & Tail-Risk Panel */}
        <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)] overflow-hidden flex flex-col justify-between">
          <div>
            <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[var(--accent-red)]" />
                STRESS-TESTING TAIL RISK
              </span>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Shock Exponent:</span>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="0.5"
                    max="2.5"
                    step="0.1"
                    value={simulationShock}
                    onChange={(e) => setSimulationShock(parseFloat(e.target.value))}
                    className="w-20 accent-[var(--accent-red)] cursor-pointer"
                  />
                  <span className="text-xs font-mono font-bold text-white">{simulationShock}x</span>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">SIMULATED CRASH IMPACT (-20% / -35%):</span>
                {advisor.worst_case_scenarios.length > 0 ? (
                  <div className="p-3 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/5 rounded space-y-1">
                    <span className="text-[10px] font-bold text-[var(--accent-red)] uppercase block">MARKET CRASH SIMULATION</span>
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-white">Estimated Loss:</span>
                      <span className="font-bold text-[var(--accent-red)]">
                        -${(advisor.worst_case_scenarios[0].estimated_loss * simulationShock).toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-white">Percentage Drop:</span>
                      <span className="font-bold text-[var(--accent-red)]">
                        -{(advisor.worst_case_scenarios[0].percentage_impact * simulationShock).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-[var(--text-muted)] font-mono">No active positions to model stress vectors.</p>
                )}
              </div>
            </div>
          </div>

          {/* ACTION CONCLUSION Badges */}
          <div className="bg-[var(--border-subtle)]/20 px-4 py-2.5 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="text-[10px] font-mono text-[var(--text-muted)]">AI DECISION CONCLUSION:</span>
            <span className={`text-[10px] font-mono font-bold tracking-widest px-2.5 py-1 rounded border uppercase ${getConclusionBadge(executiveSummary.conclusions.stress_testing)}`}>
              {executiveSummary.conclusions.stress_testing}
            </span>
          </div>
        </div>

      </div>

      {/* 4. SECTOR & CORRELATION COGNITIVE WORKSPACE (Secondary metrics, subordinate style) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Sector Distribution Detail */}
        <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)]">
          <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)]">
            <span className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-2">
              <PieChart className="w-3.5 h-3.5" />
              Exposure Distribution Details
            </span>
          </div>
          <div className="p-4 space-y-3">
            {advisor.sector_exposure.length === 0 ? (
              <div className="text-center py-4 text-[var(--text-muted)] font-mono text-xs uppercase">No active exposures</div>
            ) : (
              advisor.sector_exposure.map((exp, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-[var(--text-muted)]">{exp.sector}</span>
                    <span className="text-white">${exp.amount.toLocaleString()} ({exp.percentage}%)</span>
                  </div>
                  <div className="w-full bg-[var(--border-subtle)]/20 h-1.5 rounded overflow-hidden">
                    <div className="bg-[var(--accent-blue)]/70 h-full rounded" style={{ width: `${exp.percentage}%` }} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Correlation matrix */}
        <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)]">
          <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <span className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-2">
              <Grid3X3 className="w-3.5 h-3.5" />
              Pairwise Correlation Coefficients
            </span>
          </div>
          <div className="p-4">
            {advisor.correlation_matrix.length === 0 ? (
              <div className="text-center py-4 text-[var(--text-muted)] font-mono text-xs uppercase">No open correlations</div>
            ) : (
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                {advisor.correlation_matrix.map((item, idx) => {
                  const val = item.correlation;
                  const isHigh = val >= 0.7;
                  const colorClass = isHigh
                    ? "text-[var(--accent-red)] bg-[var(--accent-red)]/5 border-[var(--accent-red)]/20"
                    : "text-[var(--text-muted)] bg-[var(--border-subtle)]/20 border-[var(--border-subtle)]/45";
                  return (
                    <div key={idx} className={`p-2 border rounded flex justify-between items-center ${colorClass}`}>
                      <span className="font-medium">{item.asset_a} ↔ {item.asset_b}</span>
                      <span className="font-bold">{val.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 5. TOP RECOMMENDATION OPPORTUNITIES WITH WHY/EVIDENCE (Product Review Priority #3, #4) */}
      <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)]">
        <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)] flex items-center justify-between">
          <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-[var(--accent-yellow)] animate-pulse" />
            OLLO PORTFOLIO OPTIMIZATION SETUP OPPORTUNITIES
          </span>
          <span className="text-[10px] font-mono text-[var(--text-muted)]">HIGH-CONVICTION OPPORTUNITIES</span>
        </div>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {advisor.opportunity_recommendations.map((opp, idx) => (
              <div key={idx} className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)] p-4 flex flex-col justify-between space-y-3.5">
                <div className="space-y-3">
                  <div className="flex justify-between items-center border-b border-[var(--border-subtle)]/40 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white tracking-tight">{opp.symbol}</span>
                      <span className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded ${
                        opp.side === "LONG" ? "bg-[var(--accent-green)]/10 text-[var(--accent-green)]" : "bg-[var(--accent-red)]/10 text-[var(--accent-red)]"
                      }`}>
                        {opp.side}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">Setup Score: {opp.score}</span>
                  </div>

                  {/* Structured Explanation (Q&A) */}
                  <div className="space-y-2 text-xs font-mono">
                    <div>
                      <span className="text-[10px] font-bold text-[var(--accent-blue)] uppercase block mb-0.5">WHY:</span>
                      <p className="text-white leading-relaxed font-sans">{opp.why || opp.reason}</p>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-[var(--accent-yellow)] uppercase block mb-0.5">EVIDENCE SUPPORT:</span>
                      <p className="text-[var(--text-muted)] leading-relaxed font-sans">{opp.evidence || "Scanned algorithmic order structures support entry."}</p>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-[var(--accent-green)] uppercase block mb-0.5">EXPECTED BENEFIT:</span>
                      <p className="text-[var(--text-muted)] leading-relaxed font-sans">{opp.expected_benefit || "High risk-to-reward ratio expansion target hit."}</p>
                    </div>
                  </div>
                </div>
                <div className="pt-2 border-t border-[var(--border-subtle)]/40 flex justify-end">
                  <Link
                    to={opp.actionable_link}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-bold bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/80 text-white uppercase tracking-wider rounded transition-colors"
                  >
                    DEPLOY CAPITAL <PlusCircle className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* WORST-CASE DETAIL SCENARIOS CARD GRID */}
      <div className="border border-[var(--border-subtle)] rounded bg-[var(--background-card)]">
        <div className="bg-[var(--border-subtle)]/40 px-4 py-2 border-b border-[var(--border-subtle)]">
          <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-[var(--text-muted)]" />
            STRESS MODEL DETAILED ANALYSIS DISPATCHES
          </span>
        </div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {advisor.worst_case_scenarios.map((sc, idx) => (
            <div key={idx} className="border border-[var(--border-subtle)]/60 rounded bg-[var(--background-card)] p-4 flex flex-col justify-between space-y-3">
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <h5 className="text-xs font-bold text-white uppercase tracking-wider">{sc.name}</h5>
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded ${
                    sc.probability === "Low" ? "bg-[var(--accent-green)]/10 text-[var(--accent-green)]" : "bg-[var(--accent-yellow)]/10 text-[var(--accent-yellow)]"
                  }`}>
                    {sc.probability} Prob
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed font-sans">{sc.description}</p>
              </div>
              <div className="border-t border-[var(--border-subtle)]/40 pt-3 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-[var(--text-muted)] uppercase">Portfolio Impact:</span>
                  <span className="font-bold text-[var(--accent-red)]">
                    -${(sc.estimated_loss * simulationShock).toFixed(2)} (-{(sc.percentage_impact * simulationShock).toFixed(1)}%)
                  </span>
                </div>
                <div className="bg-[var(--accent-red)]/5 border-l border-[var(--accent-red)] p-2 rounded-r text-[10px] font-mono text-white">
                  <span className="font-bold uppercase block text-[var(--accent-red)] text-[9px] mb-0.5">AI Recommendation Counter-Measure:</span>
                  {sc.critical_action}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CORE TERMINAL BALANCES SECTION */}
      <div className="border-t border-[var(--border-subtle)] pt-6">
        <h3 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] font-bold mb-4">
          Institutional Balance Ledger & Performance
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <BalanceCard
            equity={port.equity}
            totalPnl={port.total_pnl}
            unrealizedPnl={port.unrealized_pnl}
          />
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="Win Rate" value={`${port.win_rate.toFixed(1)}%`} />
            <MetricCard label="Loss Rate" value={`${port.loss_rate.toFixed(1)}%`} negative />
            <MetricCard label="Total Trades" value={String(port.total_trades)} />
            <MetricCard label="Avg PnL" value={`$${port.average_pnl.toFixed(2)}`} positive={port.average_pnl >= 0} negative={port.average_pnl < 0} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="Profit Factor" value={port.profit_factor.toFixed(2)} />
            <MetricCard label="Max Drawdown" value={`${port.max_drawdown.toFixed(1)}%`} negative />
            <MetricCard label="Open Exposure" value={`$${port.current_open_exposure.toFixed(0)}`} />
            <MetricCard label="Daily PnL" value={`$${port.daily_pnl.toFixed(2)}`} positive={port.daily_pnl >= 0} negative={port.daily_pnl < 0} />
          </div>
        </div>
      </div>

      <PositionTable positions={positions} />
    </div>
  );
}

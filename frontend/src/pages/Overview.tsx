import { useCallback, useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";

import RegimeBadge from "../components/market/RegimeBadge";
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
}

function OverviewCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-[var(--border-default)] rounded-2xl p-5 shadow-[0_2px_8px_rgba(15,23,42,0.02)] transition-all duration-300 hover:shadow-[0_8px_20px_rgba(15,23,42,0.04)] hover:border-slate-300">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-3.5">
        {label}
      </h3>
      {children}
    </div>
  );
}

interface ModuleCardProps {
  number: string;
  icon: string;
  title: string;
  subtitle: string;
  color: string;
  gradient: string;
  route: string;
}

function ModuleCard({ number, icon, title, subtitle, color, gradient, route }: ModuleCardProps) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(route)}
      className="group relative text-left w-full h-full p-6 bg-white rounded-2xl border border-[var(--border-default)] transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_12px_28px_rgba(15,23,42,0.06)] active:scale-[0.98] cursor-pointer overflow-hidden flex flex-col justify-between min-h-[190px]"
    >
      {/* Soft Pastel Background Gradient */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ background: `linear-gradient(135deg, ${gradient})` }}
      />

      <div className="relative z-10 flex flex-col h-full justify-between">
        {/* Card Header: Number and Icon */}
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono font-bold text-[var(--text-muted)] group-hover:text-slate-500">
            {number}
          </span>
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold transition-all duration-300"
            style={{
              backgroundColor: `${color}12`,
              color: color,
              boxShadow: `0 0 12px ${color}15`
            }}
          >
            {icon}
          </div>
        </div>

        {/* Card Content */}
        <div className="mt-6 flex-1 flex flex-col justify-end">
          <div className="flex items-center gap-1.5">
            <h4 className="text-sm font-bold text-[var(--text-primary)] tracking-tight">
              {title}
            </h4>
            <span className="text-xs text-[var(--text-muted)] group-hover:translate-x-1.5 transition-transform duration-300">
              →
            </span>
          </div>
          <p className="text-[11px] text-[var(--text-secondary)] mt-1.5 leading-relaxed">
            {subtitle}
          </p>
        </div>
      </div>

      {/* Soft accent glow edge on active */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[3px] opacity-20 group-hover:opacity-100 transition-opacity"
        style={{ backgroundColor: color }}
      />
    </button>
  );
}

export default function Overview() {
  const { openTrades, closedTrades } = useOutletContext<LayoutContext>();
  const [market, setMarket] = useState<MarketData | null>(null);
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [perf, setPerf] = useState<PerfSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const [m, r, po] = await Promise.all([
        apiFetch<MarketData>("/market"),
        apiFetch<RiskSummary>("/risk"),
        apiFetch<PerfSummary>("/portfolio"),
      ]);
      if (m.error) {
        setError(m.error);
        return;
      }
      setMarket(m);
      setRisk(r);
      setPerf(po);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const modules = [
    {
      number: "01",
      icon: "◈",
      title: "Founder Command Center",
      subtitle: "Continuous operational brief, real-time OLLO AI briefing, and mission-critical system health indicators.",
      color: "#2563EB",
      gradient: "rgba(37, 99, 235, 0.02) 0%, rgba(37, 99, 235, 0.05) 100%",
      route: "/command-deck"
    },
    {
      number: "02",
      icon: "⚡",
      title: "Decision Intelligence",
      subtitle: "Unified AI reasoning chamber, multi-engine consensus, and dynamic validation scoring records.",
      color: "#7C3AED",
      gradient: "rgba(124, 58, 237, 0.02) 0%, rgba(124, 58, 237, 0.05) 100%",
      route: "/decisions"
    },
    {
      number: "03",
      icon: "🔍",
      title: "Scanner Room",
      subtitle: "Automated real-time technical scanners, high-frequency signal alerts, and candidate trade filters.",
      color: "#10B981",
      gradient: "rgba(16, 185, 129, 0.02) 0%, rgba(16, 185, 129, 0.05) 100%",
      route: "/scanner"
    },
    {
      number: "04",
      icon: "▣",
      title: "Portfolio Intelligence",
      subtitle: "Institutional-grade asset allocation maps, aggregate exposure controls, and comprehensive PnL analytics.",
      color: "#EA580C",
      gradient: "rgba(234, 88, 12) 0%, rgba(234, 88, 12, 0.05) 100%",
      route: "/portfolio"
    },
    {
      number: "05",
      icon: "⚙",
      title: "Strategy Lab",
      subtitle: "Visual strategy construction workspace, quantitative backtesting engine, and parameter optimizers.",
      color: "#2563EB",
      gradient: "rgba(37, 99, 235, 0.02) 0%, rgba(37, 99, 235, 0.05) 100%",
      route: "/backtest"
    },
    {
      number: "06",
      icon: "🔄",
      title: "Market Simulator",
      subtitle: "Chronological play loop simulator, synthetic scenario generator, and high-fidelity paper trading.",
      color: "#0891B2",
      gradient: "rgba(8, 145, 178, 0.02) 0%, rgba(8, 145, 178, 0.05) 100%",
      route: "/paper-trading"
    },
    {
      number: "07",
      icon: "✦",
      title: "AI Learning Center",
      subtitle: "System training, deep learning score breakdown logs, and neural pattern analysis tutorials.",
      color: "#8B5CF6",
      gradient: "rgba(139, 92, 246, 0.02) 0%, rgba(139, 92, 246, 0.05) 100%",
      route: "/ai-experience"
    },
    {
      number: "08",
      icon: "⇄",
      title: "Trade Journal",
      subtitle: "Chronological review of historical orders, execution logs, and granular post-session rater scorecards.",
      color: "#EF4444",
      gradient: "rgba(239, 68, 68, 0.02) 0%, rgba(239, 68, 68, 0.05) 100%",
      route: "/trades"
    }
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 border border-dashed border-[var(--border-default)] bg-white rounded-2xl text-center min-h-[300px]">
        <div className="w-8 h-8 border-2 border-[var(--accent-blue)] border-t-transparent rounded-full animate-spin mb-4" />
        <span className="text-[var(--text-secondary)] text-xs font-mono">Loading platform gateway...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-5 border border-[var(--accent-red)]/20 bg-red-50 rounded-2xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchAll} className="px-3 py-1.5 bg-white border border-red-200 text-red-600 font-semibold rounded-lg hover:bg-red-50 transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto pb-12">
      {/* Welcome Title Banner */}
      <div className="flex flex-col gap-1.5">
        <h2 className="text-xl font-bold tracking-tight text-slate-900">
          Platform Gateway
        </h2>
        <p className="text-xs text-[var(--text-secondary)] max-w-2xl">
          Welcome back. Select an application workspace below to access dedicated real-time telemetry, advanced simulators, or visual backtesting environments.
        </p>
      </div>

      {/* Gateway Application Module Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {modules.map((m) => (
          <ModuleCard
            key={m.number}
            number={m.number}
            icon={m.icon}
            title={m.title}
            subtitle={m.subtitle}
            color={m.color}
            gradient={m.gradient}
            route={m.route}
          />
        ))}
      </div>

      {/* Real-time Telemetry Stats Underneath */}
      <div className="space-y-4 pt-4 border-t border-slate-100">
        <h3 className="text-xs uppercase tracking-wider text-[var(--text-secondary)] font-bold">
          System Overview & Telemetry
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {market && (
            <OverviewCard label="BTC Status">
              <div className="flex items-center justify-between mb-3">
                <span className="text-lg font-bold tabular-nums text-[var(--text-primary)]">
                  ${market.price.toLocaleString(undefined, { minimumFractionDigits: 0 })}
                </span>
                <RegimeBadge regime={market.regime} />
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-50 pt-2">
                <div><span className="text-[var(--text-secondary)]">RSI</span> <span className="tabular-nums text-[var(--text-primary)] font-semibold float-right">{market.rsi.toFixed(0)}</span></div>
                <div><span className="text-[var(--text-secondary)]">Health</span> <span className="tabular-nums text-[var(--text-primary)] font-semibold float-right">{(market.btc_health_score * 100).toFixed(0)}%</span></div>
              </div>
            </OverviewCard>
          )}

          <OverviewCard label="Trades">
            <div className="text-2xl font-bold tabular-nums text-[var(--text-primary)] mb-3">
              {openTrades.length}
              <span className="text-sm text-[var(--text-secondary)] ml-1 font-normal">/ {openTrades.length + closedTrades.length} total</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-50 pt-2">
              <div><span className="text-[var(--accent-green)] font-semibold">{openTrades.length} active</span></div>
              <div><span className="text-[var(--text-secondary)] tabular-nums float-right">{closedTrades.length} completed</span></div>
            </div>
          </OverviewCard>

          {risk && (
            <OverviewCard label="Risk Assessment">
              <div className="text-2xl font-bold tabular-nums mb-3">
                <span className={risk.risk_score >= 0.5 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                  {(risk.risk_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-50 pt-2">
                <div><span className="text-[var(--text-secondary)]">Open Limit</span> <span className="tabular-nums text-[var(--text-primary)] font-semibold float-right">{risk.open_trades}/{risk.max_open_trades}</span></div>
                <div><span className="text-[var(--text-secondary)]">Daily Loss</span> <span className={`tabular-nums font-semibold float-right ${risk.daily_loss < 0 ? "text-[var(--accent-red)]" : "text-[var(--text-primary)]"}`}>${Math.abs(risk.daily_loss).toFixed(0)}</span></div>
              </div>
            </OverviewCard>
          )}

          {perf && (
            <OverviewCard label="Platform Performance">
              <div className={`text-2xl font-bold tabular-nums mb-3 ${totalPnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                ${totalPnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-50 pt-2">
                <div><span className="text-[var(--text-secondary)]">Win Rate</span> <span className="tabular-nums text-[var(--text-primary)] font-semibold float-right">{perf.win_rate.toFixed(0)}%</span></div>
                <div><span className="text-[var(--text-secondary)]">Sharpe Ratio</span> <span className="tabular-nums text-[var(--text-primary)] font-semibold float-right">{perf.sharpe_ratio.toFixed(2)}</span></div>
              </div>
            </OverviewCard>
          )}
        </div>
      </div>
    </div>
  );
}

import { useEffect } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { useTerminalStore } from "../../stores/terminal-store";

interface WorkflowStep {
  num: string;
  label: string;
  path: string;
  icon: string;
}

const steps: WorkflowStep[] = [
  { num: "01", label: "Overview", path: "/overview", icon: "◉" },
  { num: "02", label: "Intelligence", path: "/intelligence", icon: "✦" },
  { num: "03", label: "Signals", path: "/signals", icon: "⚡" },
  { num: "04", label: "Portfolio", path: "/portfolio", icon: "▣" },
  { num: "05", label: "Risk", path: "/risk", icon: "▲" },
  { num: "06", label: "OLLO", path: "/ai-experience", icon: "◆" },
];

export default function WorkflowNav() {
  const { pathname } = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { symbol: storeSymbol, setSymbol } = useTerminalStore();

  const currentSymbol = searchParams.get("symbol") || storeSymbol || "BTCUSDT";

  // Bidirectional synchronization between URL query param and terminal store
  useEffect(() => {
    const urlSymbol = searchParams.get("symbol");
    if (urlSymbol && urlSymbol !== storeSymbol) {
      setSymbol(urlSymbol);
    } else if (!urlSymbol && storeSymbol) {
      setSearchParams({ symbol: storeSymbol }, { replace: true });
    }
  }, [searchParams, storeSymbol, setSearchParams, setSymbol]);

  // If the component mounts and neither has a symbol, set default to "BTCUSDT"
  useEffect(() => {
    const urlSymbol = searchParams.get("symbol");
    if (!urlSymbol && !storeSymbol) {
      setSymbol("BTCUSDT");
      setSearchParams({ symbol: "BTCUSDT" }, { replace: true });
    }
  }, [searchParams, storeSymbol, setSearchParams, setSymbol]);

  return (
    <div className="w-full bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-3 mb-4 shadow-md font-mono">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Left Side: Context indicator */}
        <div className="flex items-center gap-3 px-2 border-r border-[var(--border-subtle)] pr-4 shrink-0">
          <div className="flex flex-col">
            <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] font-bold">
              Active Context
            </span>
            <span className="text-xs font-bold text-[var(--accent-blue)] flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-pulse" />
              {currentSymbol}
            </span>
          </div>
        </div>

        {/* Middle/Right Side: 6-Step Funnel Flow */}
        <div className="flex-1 flex flex-wrap sm:flex-nowrap items-center justify-between gap-1">
          {steps.map((step, idx) => {
            const isActive = pathname === step.path;
            const isCompleted = steps.findIndex(s => s.path === pathname) > idx;

            return (
              <div key={step.path} className="flex-1 flex items-center min-w-[110px]">
                <Link
                  to={`${step.path}?symbol=${currentSymbol}`}
                  className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-300 relative ${
                    isActive
                      ? "text-[var(--text-primary)] bg-[var(--bg-base)] border border-[var(--accent-blue)]/50 shadow-glow-blue"
                      : isCompleted
                      ? "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                  }`}
                  style={isActive ? {
                    boxShadow: "inset 0 0 12px rgba(59, 130, 246, 0.08)",
                  } : {}}
                >
                  {/* Glowing indicator on active step */}
                  {isActive && (
                    <span className="absolute right-2 top-2 w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-pulse" />
                  )}

                  {/* Step index */}
                  <span
                    className={`text-[9px] font-bold ${
                      isActive
                        ? "text-[var(--accent-blue)]"
                        : isCompleted
                        ? "text-[var(--accent-green)]"
                        : "text-[var(--text-muted)]"
                    }`}
                  >
                    {step.num}
                  </span>

                  {/* Step Content */}
                  <div className="flex flex-col items-start min-w-0">
                    <span className="text-[11px] font-bold tracking-wide truncate">
                      {step.label}
                    </span>
                    <span className="text-[8px] text-[var(--text-muted)] uppercase tracking-wider leading-none mt-0.5">
                      {isActive ? "ACTIVE" : isCompleted ? "CHECKED" : "NEXT"}
                    </span>
                  </div>
                </Link>

                {/* Arrow / Chevron Divider between steps */}
                {idx < steps.length - 1 && (
                  <span className="hidden md:block mx-1.5 text-[var(--text-muted)] opacity-40 font-bold select-none">
                    →
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

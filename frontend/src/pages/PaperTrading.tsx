import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";

import type { PaperTradingData } from "../api/paper";
import { fetchPaperTrading } from "../api/paper";
import { ApiError } from "../api/client";
import PaperPnLCard from "../components/paper/PaperPnLCard";
import PaperPerformanceCard from "../components/paper/PaperPerformanceCard";
import PaperPositionTable from "../components/paper/PaperPositionTable";

export default function PaperTrading() {
  const navigate = useNavigate();
  const [data, setData] = useState<PaperTradingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchPaperTrading();
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load paper trading");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading paper trading...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        No paper trading data
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Paper Trading Terminal</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PaperPnLCard
          totalPnl={data.performance.total_pnl}
          openTrades={data.performance.open_trades}
          closedTrades={data.performance.closed_trades}
        />
        <PaperPerformanceCard
          totalTrades={data.performance.total_trades}
          winningTrades={data.performance.winning_trades}
          losingTrades={data.performance.losing_trades}
          winRate={data.performance.win_rate}
        />
      </div>

      <PaperPositionTable trades={data.open} title="Open Trades" />
      <PaperPositionTable trades={data.closed} title="Closed Trades" />

      {/* Decision Transition Card */}
      <div className="pt-6">
        <div className="border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/5 rounded-xl p-6 space-y-4 shadow-[0_0_20px_rgba(79,140,255,0.05)]">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
              Next Decision Phase
            </span>
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              Position executed or closed?
            </h3>
            <p className="text-xs text-[var(--text-secondary)]">
              Capture the reasoning behind today's decision to improve future performance.
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => navigate("/journal")}
            className="font-bold font-mono tracking-wider uppercase"
          >
            Record Your Thinking →
          </Button>
        </div>
      </div>
    </div>
  );
}

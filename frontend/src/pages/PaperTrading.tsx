import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { PaperTradingData } from "../api/paper";
import { fetchPaperTrading } from "../api/paper";
import { ApiError } from "../api/client";
import PaperPnLCard from "../components/paper/PaperPnLCard";
import PaperPerformanceCard from "../components/paper/PaperPerformanceCard";
import PaperPositionTable from "../components/paper/PaperPositionTable";

export default function PaperTrading() {
  const { t } = useTranslation(["paperTrading", "common"]);
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
      setError(e instanceof ApiError ? e.message : t("page.loadError"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("page.loading")}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">{t("common:retry")}</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("page.noData")}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">{t("page.heading")}</h2>

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

      <PaperPositionTable trades={data.open} title={t("page.openTrades")} />
      <PaperPositionTable trades={data.closed} title={t("page.closedTrades")} />
    </div>
  );
}

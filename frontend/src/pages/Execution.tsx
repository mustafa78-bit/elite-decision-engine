import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { ExecutionData } from "../api/execution";
import { fetchExecutionStatus } from "../api/execution";
import { ApiError } from "../api/client";
import ExecutionStats from "../components/execution/ExecutionStats";
import ExecutionTimeline from "../components/execution/ExecutionTimeline";
import ErrorPanel from "../components/execution/ErrorPanel";

export default function Execution() {
  const { t } = useTranslation(["execution", "common"]);
  const [data, setData] = useState<ExecutionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchExecutionStatus();
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("execution:page.loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        {t("execution:page.loading")}
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
        {t("execution:page.noData")}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">{t("execution:page.title")}</h2>

      <ExecutionStats signals={data.signals} trades={data.trades} />

      <ExecutionTimeline
        approved={data.signals.approved}
        rejected={data.signals.rejected}
        pending={data.signals.pending}
      />

      <ErrorPanel errors={data.errors} />
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";

import type { RegimeData } from "../api/regime";
import { fetchRegime } from "../api/regime";
import { ApiError } from "../api/client";
import RegimePanel from "../components/regime/RegimePanel";

export default function Regime() {
  const [data, setData] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await fetchRegime();
      if (d.error) {
        setError(d.error);
        return;
      }
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load regime data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading regime data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)] bg-[var(--accent-red)]/10 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Market Regime</h2>
      <div className="max-w-md">
        <RegimePanel data={data} />
      </div>
    </div>
  );
}

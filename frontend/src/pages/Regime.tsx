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
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading regime data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">Market Regime</h2>
      <div className="max-w-md">
        <RegimePanel data={data} />
      </div>
    </div>
  );
}

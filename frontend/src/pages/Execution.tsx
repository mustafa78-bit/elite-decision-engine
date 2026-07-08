import { useCallback, useEffect, useState } from "react";

import type { ExecutionData } from "../api/execution";
import { fetchExecutionStatus } from "../api/execution";
import { ApiError } from "../api/client";
import ExecutionStats from "../components/execution/ExecutionStats";
import ExecutionTimeline from "../components/execution/ExecutionTimeline";
import ErrorPanel from "../components/execution/ErrorPanel";

export default function Execution() {
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
      setError(e instanceof ApiError ? e.message : "Failed to load execution status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading execution status...
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

  if (!data) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        No execution data
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">Execution Dashboard</h2>

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

import { useCallback, useEffect, useState } from "react";

import SignalTable from "../components/signals/SignalTable";
import type { SignalRow } from "../api/signals";
import { ApiError } from "../api/client";
import { fetchSignals } from "../api/signals";

export default function Signals() {
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSignals = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchSignals();
      setSignals(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load signals");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSignals(); }, [loadSignals]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading signals...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={loadSignals} className="ml-2 underline text-gray-400 hover:text-gray-200">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-gray-500">
          Signals ({signals.length})
        </h2>
        <span className="text-[10px] text-gray-600">Last {signals.length} signals</span>
      </div>
      <SignalTable signals={signals} />
    </div>
  );
}

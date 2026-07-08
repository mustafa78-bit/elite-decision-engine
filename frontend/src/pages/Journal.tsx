import { useCallback, useEffect, useState } from "react";

import type { JournalCreatePayload, JournalEntryRow } from "../api/journal";
import { createJournalEntry, deleteJournalEntry, fetchJournal } from "../api/journal";
import { ApiError } from "../api/client";

const RESULT_COLORS: Record<string, string> = {
  WIN: "text-green-400",
  LOSS: "text-red-400",
  PENDING: "text-yellow-400",
  BREAK_EVEN: "text-gray-400",
};

export default function Journal() {
  const [entries, setEntries] = useState<JournalEntryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<JournalCreatePayload>({
    symbol: "",
    side: "LONG",
    entry_price: 0,
    entry_reason: "",
  });

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchJournal();
      setEntries(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load journal");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.symbol.trim() || form.entry_price <= 0) return;
    const result = await createJournalEntry(form);
    if ("error" in result) {
      setError(result.error);
      return;
    }
    setShowForm(false);
    setForm({ symbol: "", side: "LONG", entry_price: 0, entry_reason: "" });
    load();
  };

  const handleDelete = async (id: number) => {
    const result = await deleteJournalEntry(id);
    if ("error" in result) {
      setError(result.error);
      return;
    }
    load();
  };

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading journal...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded mb-4">
        {error}
        <button onClick={load} className="ml-2 underline text-gray-400 hover:text-gray-200">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-gray-500">Trade Journal</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-[10px] uppercase tracking-wider bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1 rounded"
        >
          {showForm ? "Cancel" : "+ Entry"}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded p-4 space-y-2 max-w-lg">
          <input
            placeholder="Symbol"
            value={form.symbol}
            onChange={(e) => setForm({ ...form, symbol: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 placeholder-gray-600"
          />
          <div className="flex gap-2">
            <select
              value={form.side}
              onChange={(e) => setForm({ ...form, side: e.target.value })}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200"
            >
              <option value="LONG">LONG</option>
              <option value="SHORT">SHORT</option>
            </select>
            <input
              type="number"
              step="0.01"
              placeholder="Entry price"
              value={form.entry_price || ""}
              onChange={(e) => setForm({ ...form, entry_price: parseFloat(e.target.value) || 0 })}
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 placeholder-gray-600"
            />
          </div>
          <textarea
            placeholder="Entry reason"
            value={form.entry_reason}
            onChange={(e) => setForm({ ...form, entry_reason: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 placeholder-gray-600 min-h-[48px]"
          />
          <button
            onClick={handleCreate}
            disabled={!form.symbol.trim() || form.entry_price <= 0}
            className="text-[10px] uppercase tracking-wider bg-green-800 hover:bg-green-700 text-green-200 px-3 py-1 rounded disabled:opacity-40"
          >
            Save
          </button>
        </div>
      )}

      {entries.length === 0 && !showForm && (
        <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
          No journal entries yet
        </div>
      )}

      {entries.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-[10px] uppercase tracking-wider">
                <th className="text-left px-3 py-1.5 font-medium">Date</th>
                <th className="text-left px-3 py-1.5 font-medium">Symbol</th>
                <th className="text-left px-3 py-1.5 font-medium">Side</th>
                <th className="text-right px-3 py-1.5 font-medium">Entry</th>
                <th className="text-right px-3 py-1.5 font-medium">Score</th>
                <th className="text-right px-3 py-1.5 font-medium">Result</th>
                <th className="text-right px-3 py-1.5 font-medium">PnL</th>
                <th className="text-left px-3 py-1.5 font-medium">Reason</th>
                <th className="w-8" />
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-3 py-1.5 text-gray-500 text-[10px] tabular-nums">
                    {e.created_at ? new Date(e.created_at).toLocaleDateString() : ""}
                  </td>
                  <td className="px-3 py-1.5 text-gray-200">{e.symbol}</td>
                  <td className={`px-3 py-1.5 ${e.side === "LONG" ? "text-green-400" : "text-red-400"}`}>
                    {e.side}
                  </td>
                  <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                    {e.entry_price.toFixed(2)}
                  </td>
                  <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                    {e.score.toFixed(3)}
                  </td>
                  <td className={`px-3 py-1.5 text-right font-medium ${RESULT_COLORS[e.result] || "text-gray-300"}`}>
                    {e.result.replace("_", " ")}
                  </td>
                  <td className={`px-3 py-1.5 text-right tabular-nums ${e.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {e.pnl >= 0 ? "+" : ""}{e.pnl.toFixed(2)}
                  </td>
                  <td className="px-3 py-1.5 text-gray-500 truncate max-w-[120px]" title={e.entry_reason}>
                    {e.entry_reason}
                  </td>
                  <td className="px-2 py-1.5 text-right">
                    <button
                      onClick={() => handleDelete(e.id)}
                      className="text-gray-600 hover:text-red-400 text-[10px]"
                    >
                      x
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

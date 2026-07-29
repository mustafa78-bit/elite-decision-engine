import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchJournal, createJournalEntry, deleteJournalEntry, type JournalEntryRow } from "../api/journal";
import { ApiError } from "../api/client";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { cn } from "../lib/utils";

const RESULT_COLORS: Record<string, string> = {
  WIN: "text-[var(--accent-green)]",
  LOSS: "text-[var(--accent-red)]",
  PENDING: "text-[var(--accent-yellow)]",
  BREAK_EVEN: "text-[var(--text-secondary)]",
};

const EMOTIONS = [
  { emoji: "🧘", label: "Calm 🧘" },
  { emoji: "🤑", label: "Greedy 🤑" },
  { emoji: "😰", label: "Fearful 😰" },
  { emoji: "📈", label: "Disciplined 📈" },
  { emoji: "🎯", label: "Focused 🎯" },
];

export default function Journal() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<JournalEntryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(true); // Default open for continuous workflow
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Form states
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState("LONG");
  const [price, setPrice] = useState("");
  const [emotion, setEmotion] = useState("Calm 🧘");
  const [notes, setNotes] = useState("");
  const [attachments, setAttachments] = useState<string[]>([]);

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

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!symbol.trim() || !price) return;
    const numPrice = parseFloat(price) || 0;

    const payload = {
      symbol: symbol.toUpperCase(),
      side,
      entry_price: numPrice,
      entry_reason: notes || `Emotional state: ${emotion}`,
      notes: `Emotion: ${emotion}. Attachments: ${attachments.join(", ")}`,
      result: "PENDING",
      pnl: 0,
    };

    const result = await createJournalEntry(payload);
    if ("error" in result) {
      setError(result.error);
      return;
    }

    setSavedSuccess(true);
    // Clear form
    setSymbol("");
    setPrice("");
    setNotes("");
    setAttachments([]);
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

  const handleAddMockAttachment = () => {
    const randomAttachmentNames = [
      "h1_breakout_screenshot.png",
      "order_flow_imbalance.png",
      "btc_dominance_divergence.png",
      "volume_profile_va_edge.png",
    ];
    const nextName = randomAttachmentNames[attachments.length % randomAttachmentNames.length];
    setAttachments((prev) => [...prev, `${attachments.length + 1}_${nextName}`]);
  };

  if (loading) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Loading journal...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[9px] font-bold text-[var(--accent-blue)] uppercase tracking-widest font-mono block">
            Founder Alpha Workspace
          </span>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-primary)]">
            Executive Trade Journal
          </h2>
        </div>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setSavedSuccess(false);
          }}
          className="text-[10px] uppercase tracking-wider bg-[var(--bg-elevated)] hover:bg-[var(--bg-hover)] text-[var(--text-primary)] px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] transition-all font-mono"
        >
          {showForm ? "Hide Form" : "+ New Memory"}
        </button>
      </div>

      {error && (
        <div className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded-xl flex justify-between items-center">
          <span>{error}</span>
          <button onClick={load} className="underline text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-mono text-[10px]">Retry</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Column */}
        {showForm && (
          <div className="lg:col-span-5 space-y-4">
            <Card className="border-[var(--border-subtle)] shadow-xl bg-[var(--bg-surface)] overflow-hidden">
              <CardHeader className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30 py-3">
                <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-secondary)] flex items-center gap-1.5">
                  <span className="inline-block w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-pulse" />
                  Record Your Reflection
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {savedSuccess ? (
                  <div className="space-y-4 py-6 text-center animate-fadeIn">
                    <div className="mx-auto w-10 h-10 rounded-full bg-[var(--accent-green)]/10 text-[var(--accent-green)] flex items-center justify-center text-lg font-bold">
                      ✓
                    </div>
                    <div className="space-y-1">
                      <h4 className="text-xs font-bold text-[var(--text-primary)]">Trade Memory Captured</h4>
                      <p className="text-[10px] text-[var(--text-secondary)]">Your emotional and cognitive state is securely logged to the Decision Ledger.</p>
                    </div>
                    <div className="pt-2 flex flex-col gap-2">
                      <Button
                        variant="primary"
                        onClick={() => navigate("/decisions")}
                        className="w-full text-xs font-bold font-mono tracking-wider uppercase flex items-center justify-center gap-1.5"
                      >
                        Replay Decision
                      </Button>
                      <button
                        onClick={() => setSavedSuccess(false)}
                        className="text-[10px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] font-mono uppercase tracking-wider"
                      >
                        Log Another Trade
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3.5">
                    {/* Symbol & Side */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className="col-span-2">
                        <label className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] block mb-1 font-mono">Symbol</label>
                        <input
                          placeholder="BTCUSDT"
                          value={symbol}
                          onChange={(e) => setSymbol(e.target.value)}
                          className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
                        />
                      </div>
                      <div>
                        <label className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] block mb-1 font-mono">Side</label>
                        <select
                          value={side}
                          onChange={(e) => setSide(e.target.value)}
                          className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-2.5 py-1.5 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
                        >
                          <option value="LONG">LONG</option>
                          <option value="SHORT">SHORT</option>
                        </select>
                      </div>
                    </div>

                    {/* Entry Price */}
                    <div>
                      <label className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] block mb-1 font-mono">Entry Price ($)</label>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Price"
                        value={price}
                        onChange={(e) => setPrice(e.target.value)}
                        className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
                      />
                    </div>

                    {/* Emotional State (P0 workflow) */}
                    <div>
                      <label className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] block mb-1 font-mono">Emotional State</label>
                      <div className="flex flex-wrap gap-1.5">
                        {EMOTIONS.map((emo) => (
                          <button
                            key={emo.label}
                            type="button"
                            onClick={() => setEmotion(emo.label)}
                            className={cn(
                              "text-[10px] px-2.5 py-1 rounded-full border transition-all font-mono",
                              emotion === emo.label
                                ? "bg-[var(--accent-blue)]/10 border-[var(--accent-blue)] text-[var(--accent-blue)] font-semibold"
                                : "bg-[var(--bg-elevated)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                            )}
                          >
                            {emo.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Notes / Cognitive reasoning */}
                    <div>
                      <label className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] block mb-1 font-mono">Cognitive Reflection</label>
                      <textarea
                        placeholder="e.g. Breakout confirmed on 1h timeframe."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] min-h-[72px] focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
                      />
                    </div>

                    {/* Screenshots / Attachments (P0 Workflow) */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] font-mono">Visual Evidence</label>
                        <button
                          type="button"
                          onClick={handleAddMockAttachment}
                          className="text-[9px] uppercase text-[var(--accent-blue)] hover:underline font-mono"
                        >
                          + Mock Attachment
                        </button>
                      </div>
                      {attachments.length > 0 ? (
                        <div className="space-y-1.5">
                          {attachments.map((filename, i) => (
                            <div key={i} className="flex items-center justify-between bg-[var(--bg-elevated)] px-2.5 py-1 rounded border border-[var(--border-subtle)] text-[10px] text-[var(--text-secondary)]">
                              <span className="font-mono truncate">{filename}</span>
                              <button
                                type="button"
                                onClick={() => setAttachments(prev => prev.filter((_, idx) => idx !== i))}
                                className="text-[var(--accent-red)] hover:underline ml-1"
                              >
                                Remove
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-3 border border-dashed border-[var(--border-subtle)] rounded-lg text-[9px] text-[var(--text-muted)] font-mono">
                          No visual charts attached. Click + Mock Attachment to link proof.
                        </div>
                      )}
                    </div>

                    {/* Submit */}
                    <button
                      onClick={handleCreate}
                      disabled={!symbol.trim() || !price}
                      className="w-full py-2 bg-[var(--accent-green)]/15 border border-[var(--accent-green)]/30 hover:bg-[var(--accent-green)]/25 text-[var(--accent-green)] rounded-lg text-xs font-bold font-mono tracking-wider uppercase transition-all disabled:opacity-40"
                    >
                      Save Trade Memory
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* History / List Column */}
        <div className={cn("space-y-4", showForm ? "lg:col-span-7" : "lg:col-span-12")}>
          <Card className="border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <CardHeader className="py-3 flex flex-row items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30">
              <CardTitle className="text-xs uppercase tracking-wider text-[var(--text-secondary)]">
                Chronological Memory Archive
              </CardTitle>
              <Badge variant="info" className="text-[8px] font-mono">
                {entries.length} RECORDS
              </Badge>
            </CardHeader>
            <CardContent className="p-0">
              {entries.length === 0 ? (
                <div className="text-[var(--text-secondary)] text-xs p-12 border border-dashed border-[var(--border-subtle)] rounded-b text-center font-mono">
                  No trade journal memories archived yet.
                </div>
              ) : (
                <div className="relative w-full overflow-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[var(--border-subtle)] text-[var(--text-secondary)] text-[10px] uppercase tracking-wider bg-[var(--bg-elevated)]/20">
                        <th className="text-left px-4 py-2.5 font-medium font-mono">Date</th>
                        <th className="text-left px-4 py-2.5 font-medium font-mono">Symbol</th>
                        <th className="text-left px-4 py-2.5 font-medium font-mono">Side</th>
                        <th className="text-right px-4 py-2.5 font-medium font-mono">Entry</th>
                        <th className="text-right px-4 py-2.5 font-medium font-mono">Score</th>
                        <th className="text-right px-4 py-2.5 font-medium font-mono">Result</th>
                        <th className="text-left px-4 py-2.5 font-medium font-mono">Reason & notes</th>
                        <th className="w-8" />
                      </tr>
                    </thead>
                    <tbody>
                      {entries.map((e) => (
                        <tr key={e.id} className="border-t border-[var(--border-subtle)]/50 hover:bg-[var(--bg-hover)]/30 transition-colors">
                          <td className="px-4 py-2.5 text-[var(--text-secondary)] text-[10px] tabular-nums font-mono">
                            {e.created_at ? new Date(e.created_at).toLocaleDateString() : ""}
                          </td>
                          <td className="px-4 py-2.5 text-[var(--text-primary)] font-bold">{e.symbol}</td>
                          <td className="px-4 py-2.5">
                            <span className={cn(
                              "text-[9px] px-1.5 py-0.5 rounded font-bold font-mono",
                              e.side === "LONG" ? "bg-[var(--accent-green)]/10 text-[var(--accent-green)]" : "bg-[var(--accent-red)]/10 text-[var(--accent-red)]"
                            )}>
                              {e.side}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right text-[var(--text-primary)] font-mono tabular-nums">
                            {e.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-4 py-2.5 text-right text-[var(--text-secondary)] font-mono tabular-nums">
                            {(e.score || 0).toFixed(2)}
                          </td>
                          <td className="px-4 py-2.5 text-right">
                            <span className={cn("font-bold font-mono text-[10px]", RESULT_COLORS[e.result] || "text-[var(--text-primary)]")}>
                              {e.result}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-[var(--text-secondary)] max-w-[200px] truncate" title={e.entry_reason || ""}>
                            <span className="text-[var(--text-primary)] font-semibold block truncate">
                              {e.entry_reason}
                            </span>
                            <span className="text-[10px] text-[var(--text-muted)] font-mono block truncate">
                              {e.notes}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right">
                            <button
                              onClick={() => handleDelete(e.id)}
                              className="text-[var(--text-muted)] hover:text-[var(--accent-red)] text-[10px] font-mono p-1"
                              title="Delete Record"
                            >
                              ✕
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

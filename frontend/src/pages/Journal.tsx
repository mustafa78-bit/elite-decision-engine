import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { JournalCreatePayload, JournalEntryRow } from "../api/journal";
import { createJournalEntry, deleteJournalEntry, fetchJournal } from "../api/journal";
import { ApiError } from "../api/client";

const RESULT_COLORS: Record<string, string> = {
  WIN: "text-[var(--accent-green)] bg-[var(--accent-green)]/10 border-[var(--accent-green)]/20",
  LOSS: "text-[var(--accent-red)] bg-[var(--accent-red)]/10 border-[var(--accent-red)]/20",
  PENDING: "text-[var(--accent-yellow)] bg-[var(--accent-yellow)]/10 border-[var(--accent-yellow)]/20",
  BREAK_EVEN: "text-[var(--text-secondary)] bg-[var(--bg-elevated)] border-[var(--border-subtle)]",
};

export default function Journal() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const [entries, setEntries] = useState<JournalEntryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Extended fields stored inside notes column
  const [emotion, setEmotion] = useState("Calm");
  const [discipline, setDiscipline] = useState("10/10 Perfect");
  const [screenshotUrl, setScreenshotUrl] = useState("");

  const [form, setForm] = useState<JournalCreatePayload>({
    symbol: "",
    side: "LONG",
    entry_price: 0,
    exit_price: undefined,
    score: 0.5,
    confidence: 50,
    entry_reason: "",
    exit_reason: "",
    notes: "",
    result: "PENDING",
    pnl: 0,
  });

  const load = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchJournal();
      setEntries(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load trade journal");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Pre-fill form from URL search parameters for seamless journey from Closed Trades list
  useEffect(() => {
    const params = new URLSearchParams(search);
    const qSymbol = params.get("symbol");
    const qSide = params.get("side");
    const qEntry = params.get("entry_price");
    const qExit = params.get("exit_price");
    const qPnl = params.get("pnl");
    const qResult = params.get("result");

    if (qSymbol) {
      setForm((prev) => ({
        ...prev,
        symbol: qSymbol,
        side: qSide === "SHORT" ? "SHORT" : "LONG",
        entry_price: parseFloat(qEntry ?? "") || 0,
        exit_price: parseFloat(qExit ?? "") || undefined,
        pnl: parseFloat(qPnl ?? "") || 0,
        result: qResult || "PENDING",
        entry_reason: prev.entry_reason || `Execution post-mortem calibration for ${qSymbol}.`,
      }));
      setShowForm(true);
    }
  }, [search]);

  const handleCreate = async () => {
    if (!form.symbol.trim() || form.entry_price <= 0) return;
    try {
      setIsSubmitting(true);
      setError(null);

      // Serialize extended metadata into the notes field to respect the DB freeze
      const notesHeader = `[Emotional State: ${emotion}] [Discipline Score: ${discipline}]${screenshotUrl ? ` [Screenshot: ${screenshotUrl}]` : ""}\n`;
      const finalNotes = notesHeader + (form.notes || "");

      const payload: JournalCreatePayload = {
        ...form,
        symbol: form.symbol.trim().toUpperCase(),
        notes: finalNotes,
      };

      const result = await createJournalEntry(payload);
      if (result && "error" in result) {
        setError(result.error);
        return;
      }

      setShowForm(false);
      setForm({
        symbol: "",
        side: "LONG",
        entry_price: 0,
        exit_price: undefined,
        score: 0.5,
        confidence: 50,
        entry_reason: "",
        exit_reason: "",
        notes: "",
        result: "PENDING",
        pnl: 0,
      });
      setEmotion("Calm");
      setDiscipline("10/10 Perfect");
      setScreenshotUrl("");
      load();
    } catch {
      setError("An unexpected error occurred while saving the entry.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this journal entry?")) return;
    const result = await deleteJournalEntry(id);
    if (result && "error" in result) {
      setError(result.error);
      return;
    }
    load();
  };

  // Helper to parse notes column
  const parseExtendedNotes = (notesText: string | null) => {
    if (!notesText) return { cleanNotes: "", emotion: "N/A", discipline: "N/A", screenshot: null };
    const emotionMatch = notesText.match(/\[Emotional State:\s*([^\]]+)\]/);
    const disciplineMatch = notesText.match(/\[Discipline Score:\s*([^\]]+)\]/);
    const screenshotMatch = notesText.match(/\[Screenshot:\s*([^\]]+)\]/);

    let cleanNotes = notesText;
    cleanNotes = cleanNotes.replace(/\[Emotional State:\s*[^\]]+\]\s*/g, "");
    cleanNotes = cleanNotes.replace(/\[Discipline Score:\s*[^\]]+\]\s*/g, "");
    cleanNotes = cleanNotes.replace(/\[Screenshot:\s*[^\]]+\]\s*/g, "");

    return {
      cleanNotes: cleanNotes.trim(),
      emotion: emotionMatch ? emotionMatch[1] : "N/A",
      discipline: disciplineMatch ? disciplineMatch[1] : "N/A",
      screenshot: screenshotMatch ? screenshotMatch[1] : null,
    };
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Trade Journal</h2>
        </div>
        <div className="space-y-3" aria-label="Loading Journal entries">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-20 w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded animate-pulse flex flex-col justify-between p-4">
              <div className="flex justify-between">
                <div className="h-4 w-24 bg-[var(--text-muted)]/10 rounded" />
                <div className="h-4 w-12 bg-[var(--text-muted)]/10 rounded" />
              </div>
              <div className="h-3 w-3/4 bg-[var(--text-muted)]/10 rounded mt-2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Trade Journal</h2>
        </div>
        <div
          role="alert"
          className="text-[var(--accent-red)] text-xs p-4 border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/10 rounded flex items-center justify-between"
        >
          <span>Error loading journal: {error}</span>
          <button
            onClick={load}
            className="ml-4 underline font-medium text-[var(--accent-red)] hover:text-[var(--accent-red)]/80 focus:ring-1 focus:ring-[var(--accent-red)] rounded px-2 py-0.5"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Trade Journal</h2>
          <p className="text-[10px] text-[var(--text-muted)]">Record trade execution, psychology, and lessons learned</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-[10px] uppercase tracking-wider font-semibold bg-[var(--bg-elevated)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] px-3 py-1.5 rounded-lg transition-colors focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
        >
          {showForm ? "Cancel" : "+ New Entry"}
        </button>
      </div>

      {showForm && (
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-5 space-y-4 max-w-2xl shadow-xl animate-in fade-in slide-in-from-top-2 duration-200">
          <h3 className="text-xs uppercase font-bold tracking-wider text-[var(--text-secondary)] border-b border-[var(--border-subtle)] pb-2">
            Create Journal Entry
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Symbol *</label>
              <input
                placeholder="BTCUSDT"
                value={form.symbol}
                onChange={(e) => setForm({ ...form, symbol: e.target.value })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Side</label>
              <select
                value={form.side}
                onChange={(e) => setForm({ ...form, side: e.target.value })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              >
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Result</label>
              <select
                value={form.result}
                onChange={(e) => setForm({ ...form, result: e.target.value })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              >
                <option value="PENDING">PENDING</option>
                <option value="WIN">WIN</option>
                <option value="LOSS">LOSS</option>
                <option value="BREAK_EVEN">BREAK EVEN</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Entry Price *</label>
              <input
                type="number"
                step="0.00000001"
                placeholder="0.00"
                value={form.entry_price || ""}
                onChange={(e) => setForm({ ...form, entry_price: parseFloat(e.target.value) || 0 })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Exit Price</label>
              <input
                type="number"
                step="0.00000001"
                placeholder="0.00"
                value={form.exit_price || ""}
                onChange={(e) => setForm({ ...form, exit_price: parseFloat(e.target.value) || undefined })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">PnL ($)</label>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={form.pnl || ""}
                onChange={(e) => setForm({ ...form, pnl: parseFloat(e.target.value) || 0 })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Confidence (0-100%)</label>
              <input
                type="number"
                placeholder="50"
                value={form.confidence || ""}
                onChange={(e) => setForm({ ...form, confidence: Math.min(100, Math.max(0, parseInt(e.target.value) || 0)) })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-[var(--border-subtle)] pt-3">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Emotional State</label>
              <select
                value={emotion}
                onChange={(e) => setEmotion(e.target.value)}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              >
                <option value="Calm">Calm & Centered</option>
                <option value="Patient">Patient & Waiting</option>
                <option value="Anxious">Anxious / Stressed</option>
                <option value="Fear of Missing Out (FOMO)">FOMO (Fear of Missing Out)</option>
                <option value="Overconfident">Overconfident / Greedy</option>
                <option value="Frustrated">Frustrated / Revenge Trading</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Discipline Score</label>
              <select
                value={discipline}
                onChange={(e) => setDiscipline(e.target.value)}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              >
                <option value="10/10 Perfect">10/10 Perfect Execution</option>
                <option value="8/10 Good">8/10 Minimal Slippage</option>
                <option value="5/10 Average">5/10 Over-leveraged / Chased</option>
                <option value="2/10 Poor">2/10 Completely Deviated from Rules</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Screenshot / Chart URL (Optional)</label>
            <input
              type="url"
              placeholder="https://tradingview.com/x/..."
              value={screenshotUrl}
              onChange={(e) => setScreenshotUrl(e.target.value)}
              className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Entry Reason / Hypothesis *</label>
              <textarea
                placeholder="What parameters or technical indicators triggered this signal?"
                value={form.entry_reason}
                onChange={(e) => setForm({ ...form, entry_reason: e.target.value })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] min-h-[70px] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Notes & Key Lessons Learned</label>
              <textarea
                placeholder="Notes on the exit trigger, emotional discipline lessons, or trade feedback..."
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] min-h-[70px] focus:ring-1 focus:ring-[var(--accent-blue)] focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 border-t border-[var(--border-subtle)] pt-3">
            <button
              onClick={() => setShowForm(false)}
              className="text-[10px] uppercase tracking-wider font-semibold hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] px-4 py-2 rounded-lg border border-[var(--border-subtle)] transition-colors focus:ring-1 focus:ring-[var(--accent-blue)]"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={isSubmitting || !form.symbol.trim() || form.entry_price <= 0 || !form.entry_reason?.trim()}
              className="text-[10px] uppercase tracking-wider font-bold bg-[var(--accent-green)] hover:bg-[var(--accent-green)]/90 text-black px-5 py-2 rounded-lg disabled:opacity-40 transition-colors focus:ring-1 focus:ring-[var(--accent-green)]"
            >
              {isSubmitting ? "Saving..." : "Save Entry"}
            </button>
          </div>
        </div>
      )}

      {entries.length === 0 && !showForm && (
        <div className="bg-[var(--bg-elevated)] border border-dashed border-[var(--border-subtle)] rounded-xl py-12 px-6 text-center max-w-xl mx-auto space-y-4">
          <div className="text-3xl">📓</div>
          <div className="space-y-1">
            <p className="text-xs font-semibold text-[var(--text-primary)]">The ledger is empty</p>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
              Maintain full personal control. Record your execution reasons, psychological states, and learning cycles to calibrate your decision parameters.
            </p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="text-[10px] uppercase tracking-wider font-bold bg-[var(--bg-base)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] px-4 py-2 rounded-lg transition-colors focus:ring-1 focus:ring-[var(--accent-blue)]"
          >
            + Create First Entry
          </button>
        </div>
      )}

      {entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((entry) => {
            const { cleanNotes, emotion: parsedEmotion, discipline: parsedDiscipline, screenshot } = parseExtendedNotes(entry.notes);
            return (
              <div
                key={entry.id}
                className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl p-4 hover:border-[var(--border-strong)]/40 transition-all shadow-sm space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-subtle)]/40 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[var(--text-primary)]">{entry.symbol}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-mono font-semibold ${entry.side === "LONG" ? "text-[var(--accent-green)] bg-[var(--accent-green)]/10" : "text-[var(--accent-red)] bg-[var(--accent-red)]/10"}`}>
                      {entry.side}
                    </span>
                    <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold border ${RESULT_COLORS[entry.result] || RESULT_COLORS.PENDING}`}>
                      {entry.result.replace("_", " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)] font-mono">
                    <span>{entry.created_at ? new Date(entry.created_at).toLocaleDateString() : ""}</span>
                    <button
                      onClick={() => navigate(`/decisions?tab=replay&symbol=${entry.symbol}`)}
                      className="text-[9px] uppercase tracking-wider font-bold text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 hover:bg-[var(--accent-blue)]/20 px-2 py-0.5 rounded transition-colors"
                    >
                      Replay ⚡
                    </button>
                    <button
                      onClick={() => handleDelete(entry.id)}
                      className="text-[var(--text-muted)] hover:text-[var(--accent-red)] p-1 rounded transition-colors"
                      aria-label={`Delete ${entry.symbol} entry`}
                    >
                      ✕
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-[11px] bg-[var(--bg-base)]/40 p-3 rounded-lg border border-[var(--border-subtle)]/30">
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Entry Price</span>
                    <span className="font-mono font-semibold tabular-nums">${entry.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Exit Price</span>
                    <span className="font-mono font-semibold tabular-nums">{entry.exit_price ? `$${entry.exit_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "--"}</span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Realized PnL</span>
                    <span className={`font-mono font-semibold tabular-nums ${entry.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                      {entry.pnl >= 0 ? "+" : ""}${entry.pnl.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] block">Confidence Score</span>
                    <span className="font-mono font-semibold tabular-nums">{entry.confidence.toFixed(0)}%</span>
                  </div>
                </div>

                {/* Extended psychological indicators */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px] bg-[var(--bg-base)]/20 p-2 rounded border border-[var(--border-subtle)]/20">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[var(--text-muted)] uppercase">Psychology:</span>
                    <span className="font-medium text-[var(--text-secondary)]">{parsedEmotion}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[var(--text-muted)] uppercase">Discipline:</span>
                    <span className="font-medium text-[var(--text-secondary)]">{parsedDiscipline}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px]">
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] font-bold block mb-1">Entry Hypothesis</span>
                    <p className="text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-base)]/10 p-2.5 rounded border border-[var(--border-subtle)]/20 whitespace-pre-line min-h-[50px]">
                      {entry.entry_reason || "No hypothesis recorded."}
                    </p>
                  </div>
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] font-bold block mb-1">Lessons & Notes</span>
                    <p className="text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-base)]/10 p-2.5 rounded border border-[var(--border-subtle)]/20 whitespace-pre-line min-h-[50px]">
                      {cleanNotes || "No notes recorded."}
                    </p>
                  </div>
                </div>

                {screenshot && (
                  <div className="border-t border-[var(--border-subtle)]/30 pt-2 flex items-center justify-between text-[10px]">
                    <span className="text-[var(--text-muted)] font-mono">Attachment: Chart Screenshot</span>
                    <a
                      href={screenshot}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[var(--accent-blue)] hover:underline flex items-center gap-1"
                    >
                      View Link ↗
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

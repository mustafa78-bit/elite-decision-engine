import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { FormInput } from "../ui/form";

interface JournalEntry {
  id: string;
  symbol: string;
  side: "long" | "short";
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  date: string;
  notes: string;
  tags: string[];
  rating: 1 | 2 | 3 | 4 | 5;
}

export function TradeJournal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newNote, setNewNote] = useState("");

  const addNote = () => {
    if (!newNote.trim()) return;
    setEntries((prev) => [
      {
        id: Date.now().toString(),
        symbol: "BTC/USDT",
        side: "long",
        entryPrice: 42890,
        exitPrice: 43500,
        pnl: 610,
        date: new Date().toISOString(),
        notes: newNote,
        tags: ["scalper"],
        rating: 4,
      },
      ...prev,
    ]);
    setNewNote("");
    setShowAdd(false);
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Trade Journal</CardTitle>
          <Button variant="glass" size="sm" onClick={() => setShowAdd(!showAdd)} className="text-[10px]">
            + Add Note
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 overflow-y-auto space-y-2">
        {showAdd && (
          <div className="space-y-2 p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <FormInput
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Trade notes..."
              className="h-8 text-xs"
            />
            <div className="flex gap-1">
              <Button variant="primary" size="sm" onClick={addNote} disabled={!newNote.trim()} className="text-[10px]">
                Save
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)} className="text-[10px]">
                Cancel
              </Button>
            </div>
          </div>
        )}
        {entries.length === 0 ? (
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No journal entries yet</div>
        ) : (
          entries.map((e) => (
            <div key={e.id} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <Badge variant={e.side === "long" ? "success" : "danger"} className="text-[8px]">{e.side}</Badge>
                  <span className="text-[10px] font-mono text-[var(--text-secondary)]">{e.symbol}</span>
                  <span className="text-[9px] font-mono text-[var(--text-muted)]">${e.entryPrice} → ${e.exitPrice}</span>
                </div>
                <span className={`text-[10px] font-mono tabular-nums ${e.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {e.pnl >= 0 ? "+" : ""}${e.pnl.toFixed(2)}
                </span>
              </div>
              <p className="text-[10px] text-[var(--text-secondary)] mb-1">{e.notes}</p>
              <div className="flex items-center gap-1">
                {e.tags.map((t) => (
                  <span key={t} className="px-1 py-0.5 rounded bg-[var(--bg-elevated)] text-[8px] font-mono text-[var(--text-muted)]">
                    #{t}
                  </span>
                ))}
                <span className="text-[9px] text-[var(--accent-yellow)] ml-auto">
                  {"★".repeat(e.rating)}{"☆".repeat(5 - e.rating)}
                </span>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

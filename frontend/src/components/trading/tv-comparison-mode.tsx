import { useState } from "react";
import { Badge } from "../ui/badge";

interface ComparisonSymbol {
  symbol: string;
  color: string;
}

interface TVComparisonModeProps {
  symbols?: ComparisonSymbol[];
  onAdd?: (symbol: string) => void;
  onRemove?: (symbol: string) => void;
}

const symbolColors = [
  "var(--accent-blue)",
  "var(--accent-green)",
  "var(--accent-yellow)",
  "var(--accent-purple)",
  "var(--accent-orange)",
];

export function TVComparisonMode({
  symbols = [],
  onAdd,
  onRemove,
}: TVComparisonModeProps) {
  const [input, setInput] = useState("");

  const handleAdd = () => {
    if (input.trim() && onAdd) {
      onAdd(input.trim().toUpperCase());
      setInput("");
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="Add symbol..."
          className="flex-1 bg-[var(--bg-base)] rounded-lg px-2 py-1 text-[10px] font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-default)] focus:outline-none focus:border-[var(--accent-blue)]"
        />
        <button
          onClick={handleAdd}
          disabled={!input.trim()}
          className="px-2 py-1 rounded-lg bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] text-[10px] font-mono hover:bg-[var(--accent-blue)]/20 disabled:opacity-40 transition-all"
        >
          + Add
        </button>
      </div>
      {symbols.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {symbols.map((s, i) => (
            <div
              key={s.symbol}
              className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)]"
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: s.color || symbolColors[i % symbolColors.length] }}
              />
              <span className="text-[9px] font-mono text-[var(--text-secondary)]">
                {s.symbol}
              </span>
              <button
                onClick={() => onRemove?.(s.symbol)}
                className="text-[var(--text-muted)] hover:text-[var(--accent-red)] text-[9px] ml-0.5"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

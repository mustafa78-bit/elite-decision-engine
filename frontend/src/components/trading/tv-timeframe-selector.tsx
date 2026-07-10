import { useState } from "react";
import { cn } from "../../lib/utils";

type Timeframe = "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1d" | "1w";

interface TVTimeframeSelectorProps {
  selected?: Timeframe;
  onChange?: (tf: Timeframe) => void;
}

const timeframes: Timeframe[] = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"];

export function TVTimeframeSelector({
  selected = "1h",
  onChange,
}: TVTimeframeSelectorProps) {
  const [active, setActive] = useState<Timeframe>(selected);

  const handleSelect = (tf: Timeframe) => {
    setActive(tf);
    onChange?.(tf);
  };

  return (
    <div className="flex gap-0.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] p-0.5">
      {timeframes.map((tf) => (
        <button
          key={tf}
          onClick={() => handleSelect(tf)}
          className={cn(
            "px-2 py-1 text-[10px] font-mono rounded-md transition-all",
            active === tf
              ? "bg-[var(--accent-blue)]/15 text-[var(--accent-blue)] border border-[var(--accent-blue)]/20"
              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
          )}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}

import { useEffect, useState } from "react";

interface LiveIndicatorProps {
  active?: boolean;
}

export function LiveIndicator({ active = false }: LiveIndicatorProps) {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    if (!active) return;
    const interval = setInterval(() => setPulse((p) => !p), 1000);
    return () => clearInterval(interval);
  }, [active]);

  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`inline-block w-1.5 h-1.5 rounded-full transition-opacity ${
          active ? "bg-green-500" : "bg-gray-700"
        } ${pulse ? "opacity-100" : "opacity-50"}`}
      />
      <span className="text-[12px] font-mono uppercase tracking-widest text-[var(--text-muted)]">
        {active ? "Live" : "Offline"}
      </span>
    </div>
  );
}

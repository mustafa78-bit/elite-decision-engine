import { useRef, useState, useCallback } from "react";
import { cn } from "../../lib/utils";

interface SliderProps {
  value?: number;
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
  className?: string;
}

export function Slider({
  value = 50,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  className,
}: SliderProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [localValue, setLocalValue] = useState(value);

  const currentValue = dragging ? localValue : value;
  const pct = ((currentValue - min) / (max - min)) * 100;

  const updateValue = useCallback(
    (clientX: number) => {
      if (!ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
      const ratio = x / rect.width;
      const raw = min + ratio * (max - min);
      const stepped = Math.round(raw / step) * step;
      const clamped = Math.min(Math.max(stepped, min), max);
      setLocalValue(clamped);
      onChange?.(clamped);
    },
    [min, max, step, onChange],
  );

  const handleMouseDown = (e: React.MouseEvent) => {
    setDragging(true);
    updateValue(e.clientX);

    const handleMove = (e: MouseEvent) => updateValue(e.clientX);
    const handleUp = () => {
      setDragging(false);
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", handleUp);
    };

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", handleUp);
  };

  return (
    <div
      ref={ref}
      className={cn("relative h-1.5 rounded-full bg-[var(--bg-elevated)] cursor-pointer", className)}
      onMouseDown={handleMouseDown}
    >
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-purple)]"
        style={{ width: `${pct}%` }}
      />
      <div
        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-white border-2 border-[var(--accent-blue)] shadow-sm shadow-black/20"
        style={{ left: `${pct}%` }}
      />
    </div>
  );
}

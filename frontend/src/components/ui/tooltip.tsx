import { useRef, useState } from "react";
import { cn } from "../../lib/utils";

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
}

export function Tooltip({ content, children, side = "top" }: TooltipProps) {
  const [show, setShow] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(null);

  const sideStyles: Record<string, string> = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-1.5",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-1.5",
    left: "right-full top-1/2 -translate-y-1/2 mr-1.5",
    right: "left-full top-1/2 -translate-y-1/2 ml-1.5",
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setShow(true);
      }}
      onMouseLeave={() => {
        timeoutRef.current = setTimeout(() => setShow(false), 100);
      }}
    >
      {children}
      {show && (
        <div
          className={cn(
            "absolute z-50 px-2 py-1 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[10px] font-mono text-[var(--text-secondary)] whitespace-nowrap shadow-lg pointer-events-none",
            sideStyles[side],
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}

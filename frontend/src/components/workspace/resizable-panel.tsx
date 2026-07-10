import { useRef, useState, useCallback, type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface ResizablePanelProps {
  id: string;
  defaultSize?: number;
  minSize?: number;
  maxSize?: number;
  direction?: "horizontal" | "vertical";
  children: ReactNode;
  className?: string;
}

export function ResizablePanel({
  id,
  defaultSize = 300,
  minSize = 100,
  maxSize = 800,
  direction = "horizontal",
  children,
  className,
}: ResizablePanelProps) {
  const [size, setSize] = useState(defaultSize);
  const isDragging = useRef(false);
  const startPos = useRef(0);
  const startSize = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isDragging.current = true;
      startPos.current = direction === "horizontal" ? e.clientX : e.clientY;
      startSize.current = size;

      const handleMouseMove = (e: MouseEvent) => {
        if (!isDragging.current) return;
        const delta =
          (direction === "horizontal" ? e.clientX : e.clientY) -
          startPos.current;
        const newSize = Math.min(
          Math.max(startSize.current + delta, minSize),
          maxSize,
        );
        setSize(newSize);
      };

      const handleMouseUp = () => {
        isDragging.current = false;
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    },
    [direction, minSize, maxSize, size],
  );

  const style =
    direction === "horizontal"
      ? { width: size, minWidth: minSize, maxWidth: maxSize }
      : { height: size, minHeight: minSize, maxHeight: maxSize };

  return (
    <div
      className={cn("relative group", className)}
      style={style}
      data-panel-id={id}
    >
      {children}
      <div
        onMouseDown={handleMouseDown}
        className={cn(
          "absolute z-10 transition-colors",
          direction === "horizontal"
            ? "right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-[var(--accent-blue)]/30 active:bg-[var(--accent-blue)]/50"
            : "bottom-0 left-0 right-0 h-1 cursor-row-resize hover:bg-[var(--accent-blue)]/30 active:bg-[var(--accent-blue)]/50",
        )}
      />
    </div>
  );
}

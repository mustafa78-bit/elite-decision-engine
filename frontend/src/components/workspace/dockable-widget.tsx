import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

interface DockableWidgetProps {
  id: string;
  title: string;
  children: ReactNode;
  defaultPosition?: { x: number; y: number };
  defaultSize?: { width: number; height: number };
  onClose?: (id: string) => void;
  className?: string;
}

export function DockableWidget({
  id,
  title,
  children,
  defaultPosition = { x: 100, y: 100 },
  defaultSize = { width: 400, height: 300 },
  onClose,
  className,
}: DockableWidgetProps) {
  const [position, setPosition] = useState(defaultPosition);
  const [size] = useState(defaultSize);
  const [isDragging, setIsDragging] = useState(false);
  const dragOffset = { x: 0, y: 0 };

  const handleMouseDown = (e: React.MouseEvent, handle: "move" | "resize") => {
    if (handle === "move") {
      dragOffset.x = e.clientX - position.x;
      dragOffset.y = e.clientY - position.y;
      setIsDragging(true);

      const handleMouseMove = (e: MouseEvent) => {
        setPosition({
          x: e.clientX - dragOffset.x,
          y: e.clientY - dragOffset.y,
        });
      };

      const handleMouseUp = () => {
        setIsDragging(false);
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={cn(
        "fixed rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-2xl shadow-2xl shadow-black/30 overflow-hidden z-40",
        isDragging && "shadow-3xl",
        className,
      )}
      style={{
        left: position.x,
        top: position.y,
        width: size.width,
        height: size.height,
      }}
    >
      <div
        onMouseDown={(e) => handleMouseDown(e, "move")}
        className="flex items-center justify-between px-3 py-2 border-b border-[var(--border-subtle)] cursor-grab active:cursor-grabbing select-none"
      >
        <span className="text-[12px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          {title}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onClose?.(id)}
            className="w-4 h-4 rounded-full bg-[var(--bg-base)] border border-[var(--border-subtle)] flex items-center justify-center text-[11px] text-[var(--text-muted)] hover:text-[var(--accent-red)] hover:border-[var(--accent-red)]/50 transition-all"
          >
            ✕
          </button>
        </div>
      </div>
      <div className="p-3 overflow-auto" style={{ height: "calc(100% - 36px)" }}>
        {children}
      </div>
    </motion.div>
  );
}

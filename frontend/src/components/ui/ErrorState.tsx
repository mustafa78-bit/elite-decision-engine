import React from "react";
import { Button } from "./button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  icon?: React.ReactNode;
}

export function ErrorState({
  title = "System Alert",
  message = "Failed to load requested terminal data.",
  onRetry,
  icon,
}: ErrorStateProps) {
  return (
    <div className="border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/5 rounded-lg p-10 text-center flex flex-col items-center justify-center gap-4 max-w-lg mx-auto my-6 animate-fadeIn">
      {icon ? (
        <div className="text-3xl text-[var(--accent-red)]">{icon}</div>
      ) : (
        <div className="text-3xl text-[var(--accent-red)] animate-pulse">⚠️</div>
      )}
      <div className="space-y-1.5 max-w-xs">
        <h3 className="text-xs font-semibold tracking-wider text-[var(--accent-red)] font-mono uppercase">
          {title}
        </h3>
        <p className="text-[11px] text-[var(--text-secondary)] font-mono leading-relaxed">
          {message}
        </p>
      </div>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="border-[var(--accent-red)]/30 hover:bg-[var(--accent-red)]/10 text-[var(--accent-red)] font-mono text-[10px] uppercase tracking-widest px-4 mt-2"
        >
          Retry Connection
        </Button>
      )}
    </div>
  );
}

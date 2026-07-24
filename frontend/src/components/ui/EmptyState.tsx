import React from "react";
import { Button } from "./button";

interface EmptyStateProps {
  message?: string; // Backward compatibility fallback
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  actionButton?: {
    label: string;
    onClick: () => void;
    disabled?: boolean;
    variant?: "primary" | "secondary" | "danger" | "ghost" | "glass" | "outline";
  };
  loading?: boolean;
  error?: boolean | string | Error | null;
  noData?: boolean;
}

export function EmptyState({
  message,
  title,
  description,
  icon,
  actionButton,
  loading = false,
  error = false,
  noData = false,
}: EmptyStateProps) {
  const finalTitle = title || message || "No data available";

  // If loading, show loading representation
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center min-h-[220px] gap-4 w-full">
        <div className="relative flex items-center justify-center">
          <div className="w-10 h-10 border-2 border-[var(--border-subtle)] rounded-full animate-spin border-t-[var(--accent-blue)]" />
          <div className="absolute w-4 h-4 rounded-full bg-[var(--accent-blue)]/20 animate-pulse" />
        </div>
        <div className="space-y-1 max-w-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
            {finalTitle === "No data available" ? "Awaiting telemetry..." : finalTitle}
          </h3>
          <p className="text-[11px] text-[var(--text-muted)] font-mono">
            {description || "Synthesizing dynamic multi-factor intelligence feed."}
          </p>
        </div>
      </div>
    );
  }

  // If error, show premium error representation
  if (error) {
    const errorMsg = typeof error === "string" ? error : error instanceof Error ? error.message : "";
    return (
      <div className="border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/5 rounded-xl p-8 text-center flex flex-col items-center justify-center gap-4 min-h-[220px] max-w-2xl mx-auto w-full">
        <div className="w-10 h-10 rounded-full bg-[var(--accent-red)]/10 flex items-center justify-center border border-[var(--accent-red)]/30 text-[var(--accent-red)] animate-pulse">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-5 h-5"
          >
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div className="space-y-2 max-w-md">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
            {title || "Subsystem Unreachable"}
          </h3>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
            {description || "The core data services are currently disconnected or busy. Attempting automatic reconnection, or retry manually."}
          </p>
          {errorMsg && (
            <p className="text-[10px] font-mono text-[var(--accent-red)] opacity-80 mt-1 max-h-16 overflow-y-auto bg-black/25 p-1.5 rounded border border-[var(--accent-red)]/15">
              {errorMsg}
            </p>
          )}
        </div>
        {actionButton && (
          <Button
            variant={actionButton.variant || "danger"}
            size="sm"
            onClick={actionButton.onClick}
            disabled={actionButton.disabled}
            className="mt-2"
          >
            {actionButton.label}
          </Button>
        )}
      </div>
    );
  }

  // Standard no data / empty state representation
  return (
    <div className="border border-dashed border-[var(--border-subtle)] rounded-xl p-8 text-center flex flex-col items-center justify-center gap-4 min-h-[220px] max-w-2xl mx-auto w-full">
      {icon ? (
        <div className="text-[var(--text-muted)] opacity-65 flex items-center justify-center">
          {icon}
        </div>
      ) : (
        <div className="w-10 h-10 rounded-full bg-[var(--bg-elevated)] flex items-center justify-center border border-[var(--border-subtle)] text-[var(--text-muted)]">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-5 h-5"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="8" y1="12" x2="16" y2="12" />
          </svg>
        </div>
      )}
      <div className="space-y-1.5 max-w-md">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
          {finalTitle}
        </h3>
        <p className="text-[11px] text-[var(--text-muted)] leading-relaxed font-medium">
          {description || "The current database query yielded no matching records or real-time signals."}
        </p>
      </div>
      {actionButton && (
        <Button
          variant={actionButton.variant || "outline"}
          size="sm"
          onClick={actionButton.onClick}
          disabled={actionButton.disabled}
          className="mt-1"
        >
          {actionButton.label}
        </Button>
      )}
    </div>
  );
}

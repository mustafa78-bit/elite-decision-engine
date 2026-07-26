import React from "react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  message?: string; // fallback/alias for description for backward-compatibility
  cta?: React.ReactNode;
}

export function EmptyState({
  icon,
  title,
  description,
  message = "No data available",
  cta,
}: EmptyStateProps) {
  const displayTitle = title;
  const displayDescription = description || message;

  return (
    <div className="border border-dashed border-[var(--border-subtle)] rounded-lg p-12 text-center flex flex-col items-center justify-center gap-4 max-w-lg mx-auto my-6 bg-[var(--bg-elevated)]/10 backdrop-blur-sm animate-fadeIn">
      {icon ? (
        <div className="text-3xl text-[var(--text-secondary)]">
          {icon}
        </div>
      ) : (
        <div className="text-3xl text-[var(--text-muted)]">📂</div>
      )}
      <div className="space-y-1.5 max-w-xs">
        {displayTitle && (
          <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)] font-mono uppercase">
            {displayTitle}
          </h3>
        )}
        <p className="text-[11px] text-[var(--text-muted)] font-mono leading-relaxed">
          {displayDescription}
        </p>
      </div>
      {cta && <div className="mt-2">{cta}</div>}
    </div>
  );
}

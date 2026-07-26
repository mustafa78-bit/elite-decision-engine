import { useEffect, useState } from "react";
import { Skeleton } from "../ui/skeleton";

interface LoadingScreenProps {
  message?: string;
  variant?: "grid" | "table" | "list" | "detail" | "default";
  minHeight?: string;
}

const ELITE_MESSAGES = [
  "NEXUS is analyzing market intelligence...",
  "Evaluating real-time Whale Activity...",
  "AI Council consensus in progress...",
  "Synthesizing portfolio risk profile...",
  "Analyzing systemic risk vectors...",
  "Fetching market-regime data feeds...",
  "Validating decision signals...",
];

export function LoadingScreen({
  message,
  variant = "default",
  minHeight = "400px",
}: LoadingScreenProps) {
  const [currentMessage, setCurrentMessage] = useState(message || "Loading...");

  useEffect(() => {
    if (message) {
      setCurrentMessage(message);
      return;
    }
    let idx = -1;
    const interval = setInterval(() => {
      idx = (idx + 1) % ELITE_MESSAGES.length;
      setCurrentMessage(ELITE_MESSAGES[idx]);
    }, 2500);

    return () => clearInterval(interval);
  }, [message]);

  // Render correct skeleton based on requested layout variant to prevent layout shift
  const renderSkeleton = () => {
    switch (variant) {
      case "grid":
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-[var(--bg-elevated)]/40 border border-[var(--border-subtle)] rounded p-4 space-y-3">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-8 w-2/3" />
                <div className="space-y-1">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-5/6" />
                </div>
              </div>
            ))}
          </div>
        );
      case "table":
        return (
          <div className="border border-[var(--border-subtle)] rounded overflow-hidden w-full space-y-2 bg-[var(--bg-elevated)]/10">
            <div className="p-3 bg-[var(--bg-elevated)]/30 border-b border-[var(--border-subtle)] flex gap-4">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/4" />
            </div>
            <div className="p-4 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex gap-4 items-center">
                  <Skeleton className="h-4 w-1/5" />
                  <Skeleton className="h-4 w-1/4" />
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-4 w-1/6" />
                </div>
              ))}
            </div>
          </div>
        );
      case "list":
        return (
          <div className="space-y-3 w-full">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="p-4 border border-[var(--border-subtle)] rounded flex justify-between items-center bg-[var(--bg-elevated)]/20">
                <div className="space-y-2 flex-1 max-w-lg">
                  <Skeleton className="h-4 w-1/4" />
                  <Skeleton className="h-3 w-3/4" />
                </div>
                <Skeleton className="h-6 w-16 rounded" />
              </div>
            ))}
          </div>
        );
      case "detail":
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
            <div className="lg:col-span-2 space-y-4">
              <div className="p-4 border border-[var(--border-subtle)] rounded bg-[var(--bg-elevated)]/10 space-y-3">
                <Skeleton className="h-6 w-1/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-24 w-full rounded" />
              </div>
            </div>
            <div className="space-y-4">
              <div className="p-4 border border-[var(--border-subtle)] rounded bg-[var(--bg-elevated)]/10 space-y-3">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            </div>
          </div>
        );
      default:
        return (
          <div className="border border-[var(--border-subtle)] rounded p-6 max-w-md w-full mx-auto bg-[var(--bg-elevated)]/20 space-y-4">
            <Skeleton className="h-4 w-1/3 mx-auto" />
            <div className="space-y-2">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6 mx-auto" />
            </div>
            <div className="flex gap-2 justify-center pt-2">
              <Skeleton className="w-2 h-2 rounded-full" />
              <Skeleton className="w-2 h-2 rounded-full" />
              <Skeleton className="w-2 h-2 rounded-full" />
            </div>
          </div>
        );
    }
  };

  return (
    <div
      className="w-full flex flex-col items-center justify-center gap-6 animate-fadeIn transition-all duration-300"
      style={{ minHeight }}
    >
      <div className="w-full flex justify-center">
        {renderSkeleton()}
      </div>

      <div className="flex flex-col items-center gap-2">
        <div className="flex gap-1.5 items-center">
          <span className="w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
          <span className="w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
          <span className="w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
        <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-[0.15em] animate-pulse text-center max-w-sm px-4">
          {currentMessage}
        </p>
      </div>
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-[var(--text-muted)]"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

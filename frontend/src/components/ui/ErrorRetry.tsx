import { Button } from "./button";

interface ErrorRetryProps {
  message?: string;
  onRetry: () => void;
}

export function ErrorRetry({ message = "Something went wrong", onRetry }: ErrorRetryProps) {
  return (
    <div className="border border-[var(--accent-red)]/30 bg-[var(--accent-red)]/10 rounded-lg p-4 flex items-center justify-between">
      <span className="text-xs text-[var(--accent-red)] font-mono">{message}</span>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

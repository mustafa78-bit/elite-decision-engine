import { Button } from "./button";

interface ErrorRetryProps {
  message?: string;
  onRetry: () => void;
}

export function ErrorRetry({ message = "Something went wrong", onRetry }: ErrorRetryProps) {
  return (
    <div className="border border-red-900 bg-red-950/30 rounded p-4 flex items-center justify-between">
      <span className="text-xs text-red-400 font-mono">{message}</span>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

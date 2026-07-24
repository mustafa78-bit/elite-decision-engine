import { cn } from "../../lib/utils";

export type ConnectionState = "connected" | "disconnected" | "reconnecting" | "offline";

interface ConnectionIndicatorProps {
  status: ConnectionState;
  label?: string;
  className?: string;
}

const stateConfig: Record<ConnectionState, { color: string; pulse: boolean; defaultLabel: string }> = {
  connected: { color: "var(--accent-green)", pulse: true, defaultLabel: "Live" },
  disconnected: { color: "var(--accent-red)", pulse: false, defaultLabel: "Disconnected" },
  reconnecting: { color: "var(--accent-yellow)", pulse: true, defaultLabel: "Reconnecting..." },
  offline: { color: "var(--text-muted)", pulse: false, defaultLabel: "Offline" },
};

export function ConnectionIndicator({
  status = "connected",
  label,
  className,
}: ConnectionIndicatorProps) {
  const config = stateConfig[status];

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full",
          config.pulse && "animate-pulse",
        )}
        style={{ backgroundColor: config.color }}
      />
      <span className="text-[12px] font-mono text-[var(--text-muted)]">
        {label || config.defaultLabel}
      </span>
    </div>
  );
}

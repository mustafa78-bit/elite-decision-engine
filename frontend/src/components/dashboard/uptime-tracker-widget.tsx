import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface UptimeTrackerWidgetProps {
  uptimePercent?: number;
  currentStreak?: number;
  longestStreak?: number;
  lastDowntime?: string;
}

export function UptimeTrackerWidget({
  uptimePercent = 99.9,
  currentStreak = 0,
  longestStreak = 0,
}: UptimeTrackerWidgetProps) {
  const color =
    uptimePercent >= 99.9
      ? "var(--accent-green)"
      : uptimePercent >= 99.0
        ? "var(--accent-yellow)"
        : "var(--accent-red)";

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Uptime</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="28" fill="none" stroke="var(--bg-elevated)" strokeWidth="4" />
              <circle
                cx="32" cy="32" r="28" fill="none" stroke={color} strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={`${(uptimePercent / 100) * 176} 176`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-mono font-bold tabular-nums" style={{ color }}>
                {uptimePercent.toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <div>
              <div className="text-[9px] text-[var(--text-muted)]">Current Streak</div>
              <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
                {currentStreak > 24
                  ? `${(currentStreak / 24).toFixed(0)}d`
                  : `${currentStreak}h`}
              </div>
            </div>
            <div>
              <div className="text-[9px] text-[var(--text-muted)]">Longest Streak</div>
              <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
                {longestStreak > 24
                  ? `${(longestStreak / 24).toFixed(0)}d`
                  : `${longestStreak}h`}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

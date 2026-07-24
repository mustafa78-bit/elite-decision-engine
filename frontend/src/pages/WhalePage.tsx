import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function WhalePage() {
  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        Whale Activity
      </h2>
      <Card>
        <CardHeader>
          <CardTitle>Whale Tracker</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="text-3xl mb-4 opacity-30">🐋</div>
            <p className="text-xs text-[var(--text-muted)] font-mono uppercase tracking-widest mb-2">
              Whale Activity Monitor
            </p>
            <p className="text-[12px] text-[var(--text-muted)] max-w-md">
              Real-time whale transaction tracking and accumulation/distribution analysis.
              Requires exchange WebSocket data feed integration.
            </p>
            <span className="mt-4 px-2 py-0.5 border border-[var(--border-subtle)] rounded text-[12px] text-[var(--text-muted)] uppercase tracking-wider font-mono">
              Coming in Batch 5
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

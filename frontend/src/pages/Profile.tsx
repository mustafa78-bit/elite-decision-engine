import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";

export default function Profile() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center">
          <span className="text-lg font-mono text-[var(--text-muted)]">U</span>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[var(--text-primary)]">Commander</h1>
          <p className="text-[12px] font-mono text-[var(--text-muted)]">Unavailable</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Account</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">Plan</span>
              <span className="text-xs text-[var(--text-primary)]">Unavailable</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">API Calls (24h)</span>
              <span className="text-xs text-[var(--text-primary)]">Unavailable</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">Member Since</span>
              <span className="text-xs text-[var(--text-primary)]">Unavailable</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>API Keys</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="p-2 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[12px] font-mono text-[var(--text-muted)]">Unavailable</span>
            </div>
            <Button size="sm" variant="secondary" className="w-full text-[12px]" disabled>
              Generate New Key
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Notification Preferences</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">Trade Alerts</span>
              <span className="text-xs text-[var(--text-muted)]">Unavailable</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">Risk Warnings</span>
              <span className="text-xs text-[var(--text-muted)]">Unavailable</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">Daily Digest</span>
              <span className="text-xs text-[var(--text-muted)]">Unavailable</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Recent Activity</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="text-[12px] text-[var(--text-muted)] font-mono py-1">
              Unavailable
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

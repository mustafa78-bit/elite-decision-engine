import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";

export default function Profile() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center">
          <span className="text-lg font-mono text-[var(--text-muted)]">U</span>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[var(--text-primary)]">Trader</h1>
          <p className="text-[10px] font-mono text-[var(--text-muted)]">trader@elite.io</p>
        </div>
        <Badge variant="success" className="ml-2">Premium</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Account</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">Plan</span>
              <span className="text-xs text-[var(--text-primary)]">Enterprise</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">API Calls (24h)</span>
              <span className="text-xs text-[var(--text-primary)]">1,234 / 10,000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">Member Since</span>
              <span className="text-xs text-[var(--text-primary)]">March 2024</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>API Keys</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="p-2 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[10px] font-mono text-[var(--text-muted)]">ede_******a1b2</span>
              <Badge variant="success">Active</Badge>
            </div>
            <Button size="sm" variant="secondary" className="w-full text-[10px]">
              Generate New Key
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Notification Preferences</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">Trade Alerts</span>
              <span className="text-xs text-[var(--accent-green)]">Enabled</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">Risk Warnings</span>
              <span className="text-xs text-[var(--accent-green)]">Enabled</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">Daily Digest</span>
              <span className="text-xs text-[var(--text-muted)]">Disabled</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Recent Activity</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {["Logged in from Chrome", "API key regenerated", "Portfolio rebalanced"].map((activity) => (
              <div key={activity} className="text-[10px] text-[var(--text-secondary)] font-mono py-1 border-b border-[var(--border-subtle)] last:border-0">
                {activity}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

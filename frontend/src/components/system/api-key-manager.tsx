import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

interface APIKey {
  id: string;
  exchange: string;
  label: string;
  permissions: string[];
  status: "active" | "disabled" | "expired";
  lastUsed: string;
  created: string;
}

export function APIKeyManager() {
  const [keys, setKeys] = useState<APIKey[]>([
    { id: "1", exchange: "Binance", label: "Main Trading", permissions: ["trade", "read"], status: "active", lastUsed: "2m ago", created: "2025-12-01" },
    { id: "2", exchange: "Bybit", label: "Hedging", permissions: ["trade", "read"], status: "active", lastUsed: "15m ago", created: "2026-01-15" },
    { id: "3", exchange: "OKX", label: "Read Only", permissions: ["read"], status: "disabled", lastUsed: "2d ago", created: "2025-11-20" },
  ]);

  const toggleStatus = (id: string) => {
    setKeys((prev) =>
      prev.map((k) => (k.id === id ? { ...k, status: k.status === "active" ? "disabled" : "active" } : k))
    );
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>API Key Manager</CardTitle>
          <Badge variant="info">{keys.filter((k) => k.status === "active").length} active</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {keys.map((k) => (
          <div key={k.id} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">{k.exchange}</span>
                <span className="text-[9px] font-mono text-[var(--text-muted)]">{k.label}</span>
              </div>
              <Badge variant={k.status === "active" ? "success" : k.status === "disabled" ? "warning" : "danger"} className="text-[8px] capitalize">{k.status}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-[8px] font-mono text-[var(--text-muted)]">
                Perms: {k.permissions.join(", ")} · Last: {k.lastUsed}
              </div>
              <Button
                variant={k.status === "active" ? "ghost" : "primary"}
                className="h-5 text-[8px]"
                onClick={() => toggleStatus(k.id)}
              >
                {k.status === "active" ? "Disable" : "Enable"}
              </Button>
            </div>
          </div>
        ))}
        <Button variant="primary" className="w-full h-7 text-[10px]">+ Add API Key</Button>
      </CardContent>
    </Card>
  );
}

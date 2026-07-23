import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FormSelect } from "../ui/form";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";

interface Alert {
  id: string;
  title: string;
  description: string;
  type: string;
  severity: string;
  time: string;
  triggered: boolean;
}

interface AlertGeneratorProps {
  alerts?: Alert[];
}

export function AlertGenerator({
  alerts: initialAlerts = [],
}: AlertGeneratorProps) {
  const [selectedType, setSelectedType] = useState("all");
  const [alerts, setAlerts] = useState(initialAlerts);

  const filtered = selectedType === "all" ? alerts : alerts.filter((a) => a.type === selectedType);

  const types = Array.from(new Set(alerts.map((a) => a.type)));

  const createAlert = () => {
    const newAlert: Alert = {
      id: String(Date.now()),
      title: "New Signal Detected",
      description: `Custom alert at ${new Date().toLocaleTimeString()}`,
      type: selectedType === "all" ? "Custom" : selectedType,
      severity: "medium",
      time: "Just now",
      triggered: true,
    };
    setAlerts([newAlert, ...alerts]);
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Alert Generator</CardTitle>
          <Badge variant="info">{filtered.length} active</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex gap-2">
          <FormSelect value={selectedType} onChange={(e) => setSelectedType(e.target.value)} className="flex-1 h-7 text-[10px]">
            <option value="all">All Types</option>
            {types.map((t) => <option key={t} value={t}>{t}</option>)}
          </FormSelect>
          <Button variant="primary" className="h-7 text-[10px] whitespace-nowrap" onClick={createAlert}>+ New</Button>
        </div>
        {filtered.map((a) => (
          <div key={a.id} className={`p-2 rounded-lg border text-[10px] font-mono ${a.triggered ? "bg-[var(--bg-base)] border-[var(--border-subtle)]" : "bg-[var(--bg-hover)]/50 border-[var(--border-subtle)] "}`}>
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${a.severity === "high" ? "bg-[var(--accent-red)]" : a.severity === "medium" ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-blue)]"}`} />
                <span className="text-[var(--text-secondary)]">{a.title}</span>
                <Badge variant={a.severity === "high" ? "danger" : a.severity === "medium" ? "warning" : "info"} className="text-[8px]">{a.severity}</Badge>
              </div>
              <span className="text-[8px] text-[var(--text-muted)]">{a.time}</span>
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">{a.description}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

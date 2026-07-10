import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { FormInput, FormSelect } from "../ui/form";

export function SystemSettings() {
  return (
    <Card className="h-full">
      <CardHeader><CardTitle>System Settings</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Instance Name</label>
            <FormInput value="Elite Terminal" className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Environment</label>
            <FormSelect value="production" className="h-7 text-[10px]">
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </FormSelect>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Default Leverage</label>
            <FormInput value="3x" className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Max Position Size</label>
            <FormInput value="10 BTC" className="h-7 text-[10px]" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">Slippage Tolerance</label>
            <FormInput value="0.1%" className="h-7 text-[10px]" />
          </div>
          <div className="space-y-1">
            <label className="text-[9px] font-mono text-[var(--text-muted)]">UI Update Interval</label>
            <FormSelect value="1000" className="h-7 text-[10px]">
              <option value="500">500ms</option>
              <option value="1000">1s</option>
              <option value="2000">2s</option>
              <option value="5000">5s</option>
            </FormSelect>
          </div>
        </div>
        <Button variant="primary" className="w-full h-7 text-[10px] mt-2">Save Settings</Button>
      </CardContent>
    </Card>
  );
}

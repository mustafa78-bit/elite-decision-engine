import { motion } from "framer-motion";
import { WorkspaceManager } from "../components/workspace/workspace-manager";
import { ResizablePanel } from "../components/workspace/resizable-panel";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function ProfessionalWorkspace() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-4"
      >
        <h1 className="text-sm font-medium text-[var(--text-primary)]">
          Professional Workspace
        </h1>
        <WorkspaceManager />
      </motion.div>

      <div className="flex gap-4 h-[calc(100vh-12rem)]">
        <ResizablePanel id="sidebar" defaultSize={280} minSize={200} maxSize={500}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Instruments</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {["BTC/USDT", "ETH/USDT", "SOL/USDT", "LINK/USDT", "AVAX/USDT", "DOT/USDT"].map((s) => (
                  <button
                    key={s}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
                  >
                    <span>{s}</span>
                    <span className="text-[var(--accent-green)]">+2.34%</span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </ResizablePanel>

        <div className="flex-1 grid grid-rows-2 gap-4">
          <ResizablePanel id="chart" defaultSize={400} minSize={200} maxSize={600} direction="vertical">
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Chart</CardTitle>
              </CardHeader>
              <CardContent className="flex items-center justify-center h-[calc(100%-3rem)] text-sm text-[var(--text-muted)]">
                Chart panel — resize handle below
              </CardContent>
            </Card>
          </ResizablePanel>

          <Card className="h-full">
            <CardHeader>
              <CardTitle>Order Book</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-center h-[calc(100%-3rem)] text-sm text-[var(--text-muted)]">
              Order book feed
            </CardContent>
          </Card>
        </div>

        <ResizablePanel id="right-panel" defaultSize={320} minSize={240} maxSize={500}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Order Panel</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-center h-[calc(100%-3rem)] text-sm text-[var(--text-muted)]">
              Place orders here
            </CardContent>
          </Card>
        </ResizablePanel>
      </div>
    </div>
  );
}

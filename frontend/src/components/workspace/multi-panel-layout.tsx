import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface PanelConfig {
  id: string;
  type: "main" | "sidebar" | "bottom" | "floating";
  children: ReactNode;
  defaultWidth?: number;
  defaultHeight?: number;
  className?: string;
}

interface MultiPanelLayoutProps {
  panels: PanelConfig[];
  className?: string;
}

export function MultiPanelLayout({ panels, className }: MultiPanelLayoutProps) {
  const mainPanels = panels.filter((p) => p.type === "main");
  const sidebarPanels = panels.filter((p) => p.type === "sidebar");
  const bottomPanels = panels.filter((p) => p.type === "bottom");
  const floatingPanels = panels.filter((p) => p.type === "floating");

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex flex-1 min-h-0">
        {sidebarPanels.length > 0 && (
          <div className="flex flex-col gap-2 w-64 shrink-0 border-r border-[var(--border-subtle)] p-2 overflow-y-auto">
            {sidebarPanels.map((p) => (
              <div
                key={p.id}
                className={cn("rounded-xl bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)] overflow-hidden", p.className)}
              >
                {p.children}
              </div>
            ))}
          </div>
        )}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 grid gap-2 p-2 auto-rows-fr">
            {mainPanels.map((p) => (
              <div
                key={p.id}
                className={cn(
                  "rounded-xl bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)] overflow-hidden",
                  p.className,
                )}
                style={{
                  gridColumn: p.defaultWidth ? `span ${Math.min(p.defaultWidth, 4)}` : undefined,
                }}
              >
                {p.children}
              </div>
            ))}
          </div>
          {bottomPanels.length > 0 && (
            <div className="flex gap-2 p-2 border-t border-[var(--border-subtle)]">
              {bottomPanels.map((p) => (
                <div
                  key={p.id}
                  className={cn("flex-1 rounded-xl bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)] overflow-hidden", p.className)}
                  style={{ height: p.defaultHeight || 200 }}
                >
                  {p.children}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      {floatingPanels.map((p) => (
        <div
          key={p.id}
          className={cn("fixed z-50 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-default)] backdrop-blur-2xl shadow-2xl overflow-hidden", p.className)}
        >
          {p.children}
        </div>
      ))}
    </div>
  );
}
